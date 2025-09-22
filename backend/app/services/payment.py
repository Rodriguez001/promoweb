"""
Payment service for PromoWeb Africa.
Handles multiple payment gateways: Stripe, Orange Money, MTN Mobile Money.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
import uuid
import httpx
import stripe

from app.core.config import get_settings
from app.core.database import get_db_context
from app.models.payment import Payment, PaymentTransaction, payment_status_enum, payment_gateway_enum
from app.models.order import Order
from app.services.notifications import notification_service

logger = logging.getLogger(__name__)
settings = get_settings()

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    INITIATED = "initiated"
    PROCESSING = "processing"
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    EXPIRED = "expired"
    REFUNDED = "refunded"


class PaymentGateway(str, Enum):
    """Payment gateway enumeration."""
    STRIPE = "stripe"
    ORANGE_MONEY = "orange_money"
    MTN_MOBILE_MONEY = "mtn_mobile_money"
    CASH_ON_DELIVERY = "cash_on_delivery"


@dataclass
class PaymentRequest:
    """Payment request data."""
    order_id: str
    amount: Decimal
    currency: str = "XAF"
    gateway: PaymentGateway = PaymentGateway.STRIPE
    customer_email: str = None
    customer_phone: str = None
    metadata: Dict[str, Any] = None
    is_partial: bool = False


@dataclass
class PaymentResult:
    """Payment processing result."""
    success: bool
    payment_id: str
    transaction_id: Optional[str] = None
    status: PaymentStatus = PaymentStatus.FAILED
    gateway_response: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    redirect_url: Optional[str] = None
    requires_action: bool = False


class StripePaymentProcessor:
    """Stripe payment processor."""
    
    def __init__(self):
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    
    async def create_payment_intent(self, payment_request: PaymentRequest) -> PaymentResult:
        """Create Stripe payment intent."""
        try:
            # Convert XAF to cents (Stripe uses smallest currency unit)
            amount_cents = int(payment_request.amount * 100)
            
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="xaf",
                automatic_payment_methods={
                    'enabled': True,
                },
                metadata={
                    'order_id': payment_request.order_id,
                    'customer_email': payment_request.customer_email or '',
                    **(payment_request.metadata or {})
                }
            )
            
            # Store payment in database
            async with get_db_context() as db:
                payment = Payment(
                    order_id=payment_request.order_id,
                    gateway=PaymentGateway.STRIPE,
                    amount=payment_request.amount,
                    currency=payment_request.currency,
                    status=PaymentStatus.INITIATED,
                    gateway_payment_id=intent.id,
                    transaction_id=f"stripe_{intent.id}",
                    metadata={
                        'stripe_client_secret': intent.client_secret,
                        'stripe_status': intent.status
                    }
                )
                db.add(payment)
                await db.commit()
                await db.refresh(payment)
            
            logger.info(f"Stripe payment intent created: {intent.id}")
            
            return PaymentResult(
                success=True,
                payment_id=str(payment.id),
                transaction_id=intent.id,
                status=PaymentStatus.INITIATED,
                gateway_response={
                    'client_secret': intent.client_secret,
                    'payment_intent_id': intent.id
                },
                requires_action=True
            )
            
        except stripe.StripeError as e:
            logger.error(f"Stripe payment failed: {e}")
            return PaymentResult(
                success=False,
                payment_id="",
                error_message=str(e),
                status=PaymentStatus.FAILED
            )
    
    async def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Handle Stripe webhook."""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                await self._handle_payment_success(payment_intent)
            
            elif event['type'] == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                await self._handle_payment_failure(payment_intent)
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"Stripe webhook error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _handle_payment_success(self, payment_intent: Dict[str, Any]):
        """Handle successful payment."""
        async with get_db_context() as db:
            # Find payment by gateway payment ID
            from sqlalchemy import select, update
            
            result = await db.execute(
                select(Payment).where(Payment.gateway_payment_id == payment_intent['id'])
            )
            payment = result.scalar_one_or_none()
            
            if payment:
                # Update payment status
                await db.execute(
                    update(Payment)
                    .where(Payment.id == payment.id)
                    .values(
                        status=PaymentStatus.SUCCESS,
                        gateway_response=payment_intent,
                        completed_at=datetime.utcnow()
                    )
                )
                
                # Get order for notifications
                order = await db.get(Order, payment.order_id)
                if order and order.user:
                    # Send payment success notification
                    await notification_service.send_payment_success(
                        user_email=order.user.email,
                        user_phone=order.user.phone,
                        order=order,
                        payment_amount=float(payment.amount)
                    )
                
                await db.commit()
                logger.info(f"Payment marked as successful: {payment.id}")
    
    async def _handle_payment_failure(self, payment_intent: Dict[str, Any]):
        """Handle failed payment."""
        async with get_db_context() as db:
            from sqlalchemy import select, update
            
            result = await db.execute(
                select(Payment).where(Payment.gateway_payment_id == payment_intent['id'])
            )
            payment = result.scalar_one_or_none()
            
            if payment:
                await db.execute(
                    update(Payment)
                    .where(Payment.id == payment.id)
                    .values(
                        status=PaymentStatus.FAILED,
                        gateway_response=payment_intent,
                        failure_reason=payment_intent.get('last_payment_error', {}).get('message')
                    )
                )
                await db.commit()
                logger.info(f"Payment marked as failed: {payment.id}")


class MobileMoneyProcessor:
    """Mobile Money processor for Orange Money and MTN."""
    
    def __init__(self):
        self.orange_api_url = settings.ORANGE_MONEY_API_URL
        self.orange_api_key = settings.ORANGE_MONEY_MERCHANT_KEY
        self.mtn_api_url = settings.MTN_MOMO_API_URL
        self.mtn_api_key = settings.MTN_MOMO_API_KEY
    
    async def initiate_orange_money_payment(self, payment_request: PaymentRequest) -> PaymentResult:
        """Initiate Orange Money payment."""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "amount": float(payment_request.amount),
                    "currency": "XAF",
                    "phone_number": payment_request.customer_phone,
                    "reference": f"PMW_{payment_request.order_id}_{uuid.uuid4().hex[:8]}",
                    "description": f"Payment for order {payment_request.order_id}",
                    "callback_url": f"{settings.API_BASE_URL}/api/v1/payments/webhooks/orange-money"
                }
                
                headers = {
                    "Authorization": f"Bearer {self.orange_api_key}",
                    "Content-Type": "application/json"
                }
                
                response = await client.post(
                    f"{self.orange_api_url}/payments/initiate",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Store payment in database
                async with get_db_context() as db:
                    payment = Payment(
                        order_id=payment_request.order_id,
                        gateway=PaymentGateway.ORANGE_MONEY,
                        amount=payment_request.amount,
                        currency=payment_request.currency,
                        status=PaymentStatus.PENDING,
                        gateway_payment_id=result.get('transaction_id'),
                        transaction_id=payload['reference'],
                        metadata=result
                    )
                    db.add(payment)
                    await db.commit()
                    await db.refresh(payment)
                
                logger.info(f"Orange Money payment initiated: {result.get('transaction_id')}")
                
                return PaymentResult(
                    success=True,
                    payment_id=str(payment.id),
                    transaction_id=result.get('transaction_id'),
                    status=PaymentStatus.PENDING,
                    gateway_response=result
                )
                
        except Exception as e:
            logger.error(f"Orange Money payment failed: {e}")
            return PaymentResult(
                success=False,
                payment_id="",
                error_message=str(e),
                status=PaymentStatus.FAILED
            )
    
    async def initiate_mtn_money_payment(self, payment_request: PaymentRequest) -> PaymentResult:
        """Initiate MTN Mobile Money payment."""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "amount": float(payment_request.amount),
                    "currency": "XAF", 
                    "externalId": f"PMW_{payment_request.order_id}_{uuid.uuid4().hex[:8]}",
                    "payer": {
                        "partyIdType": "MSISDN",
                        "partyId": payment_request.customer_phone
                    },
                    "payerMessage": f"Payment for PromoWeb order {payment_request.order_id}",
                    "payeeNote": f"Order {payment_request.order_id}"
                }
                
                headers = {
                    "Authorization": f"Bearer {self.mtn_api_key}",
                    "X-Reference-Id": str(uuid.uuid4()),
                    "X-Target-Environment": settings.MTN_ENVIRONMENT,
                    "Content-Type": "application/json"
                }
                
                response = await client.post(
                    f"{self.mtn_api_url}/collection/v1_0/requesttopay",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                transaction_id = headers["X-Reference-Id"]
                
                # Store payment in database
                async with get_db_context() as db:
                    payment = Payment(
                        order_id=payment_request.order_id,
                        gateway=PaymentGateway.MTN_MOBILE_MONEY,
                        amount=payment_request.amount,
                        currency=payment_request.currency,
                        status=PaymentStatus.PENDING,
                        gateway_payment_id=transaction_id,
                        transaction_id=payload['externalId'],
                        metadata=payload
                    )
                    db.add(payment)
                    await db.commit()
                    await db.refresh(payment)
                
                logger.info(f"MTN Mobile Money payment initiated: {transaction_id}")
                
                return PaymentResult(
                    success=True,
                    payment_id=str(payment.id),
                    transaction_id=transaction_id,
                    status=PaymentStatus.PENDING,
                    gateway_response={"reference_id": transaction_id}
                )
                
        except Exception as e:
            logger.error(f"MTN Mobile Money payment failed: {e}")
            return PaymentResult(
                success=False,
                payment_id="",
                error_message=str(e),
                status=PaymentStatus.FAILED
            )


class PaymentService:
    """Main payment service orchestrating all payment gateways."""
    
    def __init__(self):
        self.stripe_processor = StripePaymentProcessor()
        self.mobile_money_processor = MobileMoneyProcessor()
    
    async def process_payment(self, payment_request: PaymentRequest) -> PaymentResult:
        """Process payment based on gateway."""
        logger.info(f"Processing payment for order {payment_request.order_id} via {payment_request.gateway}")
        
        try:
            if payment_request.gateway == PaymentGateway.STRIPE:
                return await self.stripe_processor.create_payment_intent(payment_request)
            
            elif payment_request.gateway == PaymentGateway.ORANGE_MONEY:
                return await self.mobile_money_processor.initiate_orange_money_payment(payment_request)
            
            elif payment_request.gateway == PaymentGateway.MTN_MOBILE_MONEY:
                return await self.mobile_money_processor.initiate_mtn_money_payment(payment_request)
            
            elif payment_request.gateway == PaymentGateway.CASH_ON_DELIVERY:
                return await self._process_cash_on_delivery(payment_request)
            
            else:
                return PaymentResult(
                    success=False,
                    payment_id="",
                    error_message="Unsupported payment gateway",
                    status=PaymentStatus.FAILED
                )
                
        except Exception as e:
            logger.error(f"Payment processing failed: {e}")
            return PaymentResult(
                success=False,
                payment_id="",
                error_message=str(e),
                status=PaymentStatus.FAILED
            )
    
    async def _process_cash_on_delivery(self, payment_request: PaymentRequest) -> PaymentResult:
        """Process cash on delivery payment."""
        try:
            async with get_db_context() as db:
                payment = Payment(
                    order_id=payment_request.order_id,
                    gateway=PaymentGateway.CASH_ON_DELIVERY,
                    amount=payment_request.amount,
                    currency=payment_request.currency,
                    status=PaymentStatus.PENDING,
                    transaction_id=f"cod_{payment_request.order_id}_{uuid.uuid4().hex[:8]}",
                    metadata={"type": "cash_on_delivery"}
                )
                db.add(payment)
                await db.commit()
                await db.refresh(payment)
            
            return PaymentResult(
                success=True,
                payment_id=str(payment.id),
                transaction_id=payment.transaction_id,
                status=PaymentStatus.PENDING
            )
            
        except Exception as e:
            logger.error(f"Cash on delivery processing failed: {e}")
            return PaymentResult(
                success=False,
                payment_id="",
                error_message=str(e),
                status=PaymentStatus.FAILED
            )
    
    async def calculate_partial_payment(self, order_amount: Decimal) -> Dict[str, Decimal]:
        """Calculate partial payment amounts (30% down payment)."""
        down_payment_percentage = Decimal('0.30')  # 30%
        
        down_payment = order_amount * down_payment_percentage
        remaining_balance = order_amount - down_payment
        
        # Round to nearest 100 XAF
        down_payment = Decimal(int(down_payment / 100) * 100)
        remaining_balance = order_amount - down_payment
        
        return {
            "down_payment": down_payment,
            "remaining_balance": remaining_balance,
            "down_payment_percentage": down_payment_percentage * 100
        }
    
    async def create_refund(self, payment_id: str, amount: Optional[Decimal] = None, reason: str = "") -> PaymentResult:
        """Create refund for a payment."""
        try:
            async with get_db_context() as db:
                from sqlalchemy import select
                
                # Get original payment
                result = await db.execute(
                    select(Payment).where(Payment.id == payment_id)
                )
                payment = result.scalar_one_or_none()
                
                if not payment:
                    return PaymentResult(
                        success=False,
                        payment_id=payment_id,
                        error_message="Payment not found",
                        status=PaymentStatus.FAILED
                    )
                
                refund_amount = amount or payment.amount
                
                if payment.gateway == PaymentGateway.STRIPE:
                    # Process Stripe refund
                    refund = stripe.Refund.create(
                        payment_intent=payment.gateway_payment_id,
                        amount=int(refund_amount * 100),  # Convert to cents
                        reason='requested_by_customer',
                        metadata={'reason': reason}
                    )
                    
                    # Record refund in database
                    from app.models.payment import PaymentRefund
                    payment_refund = PaymentRefund(
                        payment_id=payment.id,
                        amount=refund_amount,
                        reason=reason,
                        gateway_refund_id=refund.id,
                        status="completed"
                    )
                    db.add(payment_refund)
                    await db.commit()
                    
                    logger.info(f"Stripe refund processed: {refund.id}")
                    
                    return PaymentResult(
                        success=True,
                        payment_id=payment_id,
                        transaction_id=refund.id,
                        status=PaymentStatus.REFUNDED
                    )
                
                else:
                    # For mobile money, manual refund process
                    from app.models.payment import PaymentRefund
                    payment_refund = PaymentRefund(
                        payment_id=payment.id,
                        amount=refund_amount,
                        reason=reason,
                        status="pending_manual_processing"
                    )
                    db.add(payment_refund)
                    await db.commit()
                    
                    return PaymentResult(
                        success=True,
                        payment_id=payment_id,
                        status=PaymentStatus.PENDING,
                        gateway_response={"requires_manual_processing": True}
                    )
                    
        except Exception as e:
            logger.error(f"Refund processing failed: {e}")
            return PaymentResult(
                success=False,
                payment_id=payment_id,
                error_message=str(e),
                status=PaymentStatus.FAILED
            )
    
    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Get current payment status."""
        try:
            async with get_db_context() as db:
                from sqlalchemy import select
                
                result = await db.execute(
                    select(Payment).where(Payment.id == payment_id)
                )
                payment = result.scalar_one_or_none()
                
                if not payment:
                    return {"status": "not_found"}
                
                return {
                    "payment_id": str(payment.id),
                    "status": payment.status,
                    "amount": float(payment.amount),
                    "currency": payment.currency,
                    "gateway": payment.gateway,
                    "created_at": payment.created_at.isoformat(),
                    "completed_at": payment.completed_at.isoformat() if payment.completed_at else None
                }
                
        except Exception as e:
            logger.error(f"Failed to get payment status: {e}")
            return {"status": "error", "message": str(e)}


# Global payment service instance
payment_service = PaymentService()


# Convenience functions
async def process_payment(payment_request: PaymentRequest) -> PaymentResult:
    """Process a payment."""
    return await payment_service.process_payment(payment_request)


async def calculate_partial_payment(order_amount: Decimal) -> Dict[str, Decimal]:
    """Calculate partial payment amounts."""
    return await payment_service.calculate_partial_payment(order_amount)


async def create_refund(payment_id: str, amount: Optional[Decimal] = None, reason: str = "") -> PaymentResult:
    """Create a refund."""
    return await payment_service.create_refund(payment_id, amount, reason)
