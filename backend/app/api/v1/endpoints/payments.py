"""
Payment endpoints for PromoWeb Africa.
Handles payment processing, webhooks, and refunds.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from decimal import Decimal
import json
import logging

from app.api.dependencies import (
    get_current_user, get_current_admin_user, get_pagination_params,
    get_db_session
)
from app.models.payment import Payment, PaymentRefund, PaymentWebhook, PaymentMethod
from app.models.order import Order
from app.schemas.payment import (
    PaymentResponse, PaymentCreateRequest, PaymentIntentResponse, 
    PaymentRefundCreate, PaymentRefundResponse, PaymentStatusResponse,
    PartialPaymentCalculation
)
from app.schemas.common import BaseResponse, PaginatedResponse
from app.core.database import get_db_context
from app.services.payment import (
    payment_service, PaymentRequest, PaymentGateway, PaymentStatus,
    process_payment, calculate_partial_payment, create_refund
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[PaymentResponse])
async def get_user_payments(
    current_user: object = Depends(get_current_user),
    order_id: Optional[str] = None
):
    """
    Get current user's payments.
    
    - **order_id**: Filter by specific order (optional)
    """
    try:
        async with get_db_context() as db:
            # Build query to get payments for user's orders
            query = (
                select(Payment)
                .join(Order)
                .where(Order.user_id == current_user.id)
            )
            
            if order_id:
                query = query.where(Payment.order_id == order_id)
            
            result = await db.execute(
                query.options(selectinload(Payment.order))
                .order_by(Payment.created_at.desc())
            )
            payments = result.scalars().all()
            
            return [PaymentResponse.from_orm(payment) for payment in payments]
            
    except Exception as e:
        logger.error(f"Failed to get user payments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payments"
        )


@router.post("/create", response_model=PaymentIntentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_request: PaymentCreateRequest,
    current_user: object = Depends(get_current_user)
):
    """
    Create a payment for an order.
    
    - **order_id**: Order to pay for
    - **gateway**: Payment gateway to use
    - **is_partial**: Whether this is a partial payment (30% down payment)
    """
    try:
        async with get_db_context() as db:
            # Verify order exists and belongs to user
            order = await db.execute(
                select(Order)
                .where(Order.id == payment_request.order_id, Order.user_id == current_user.id)
            )
            order = order.scalar_one_or_none()
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            # Check if order can be paid
            if order.status in ['cancelled', 'refunded']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot pay for cancelled or refunded order"
                )
            
            # Calculate payment amount
            if payment_request.is_partial:
                partial_calc = await calculate_partial_payment(order.total_amount)
                payment_amount = partial_calc['down_payment']
            else:
                payment_amount = order.total_amount
            
            # Create payment request
            pay_request = PaymentRequest(
                order_id=str(order.id),
                amount=payment_amount,
                currency="XAF",
                gateway=PaymentGateway(payment_request.gateway),
                customer_email=current_user.email,
                customer_phone=current_user.phone,
                is_partial=payment_request.is_partial,
                metadata={
                    "user_id": str(current_user.id),
                    "order_number": order.order_number
                }
            )
            
            # Process payment
            result = await process_payment(pay_request)
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error_message or "Payment processing failed"
                )
            
            return PaymentIntentResponse(
                payment_id=result.payment_id,
                status=result.status.value,
                gateway=payment_request.gateway,
                amount=payment_amount,
                currency="XAF",
                gateway_response=result.gateway_response,
                requires_action=result.requires_action,
                redirect_url=result.redirect_url
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment creation failed"
        )


@router.get("/calculate-partial/{order_id}", response_model=PartialPaymentCalculation)
async def calculate_partial_payment_endpoint(
    order_id: str,
    current_user: object = Depends(get_current_user)
):
    """
    Calculate partial payment amounts for an order.
    
    Returns 30% down payment and remaining balance.
    """
    try:
        async with get_db_context() as db:
            order = await db.execute(
                select(Order)
                .where(Order.id == order_id, Order.user_id == current_user.id)
            )
            order = order.scalar_one_or_none()
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            calculation = await calculate_partial_payment(order.total_amount)
            
            return PartialPaymentCalculation(
                order_id=order_id,
                total_amount=order.total_amount,
                down_payment=calculation['down_payment'],
                remaining_balance=calculation['remaining_balance'],
                down_payment_percentage=calculation['down_payment_percentage']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate partial payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate partial payment"
        )


@router.get("/status/{payment_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    payment_id: str,
    current_user: object = Depends(get_current_user)
):
    """
    Get payment status.
    """
    try:
        async with get_db_context() as db:
            payment = await db.execute(
                select(Payment)
                .join(Order)
                .where(
                    Payment.id == payment_id,
                    Order.user_id == current_user.id
                )
                .options(selectinload(Payment.order))
            )
            payment = payment.scalar_one_or_none()
            
            if not payment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found"
                )
            
            return PaymentStatusResponse(
                payment_id=str(payment.id),
                status=payment.status,
                gateway=payment.gateway,
                amount=payment.amount,
                currency=payment.currency,
                transaction_id=payment.transaction_id,
                created_at=payment.created_at,
                completed_at=payment.completed_at,
                failure_reason=payment.failure_reason
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get payment status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment status"
        )


# Webhook endpoints
@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """
    Handle Stripe webhooks.
    """
    try:
        payload = await request.body()
        
        result = await payment_service.stripe_processor.handle_webhook(
            payload, stripe_signature
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook processing failed"
        )


@router.post("/webhooks/orange-money")
async def orange_money_webhook(request: Request):
    """
    Handle Orange Money webhooks.
    """
    try:
        payload = await request.json()
        
        # Process Orange Money webhook
        transaction_id = payload.get('transaction_id')
        status = payload.get('status')
        
        if transaction_id and status:
            async with get_db_context() as db:
                # Find payment by gateway payment ID
                result = await db.execute(
                    select(Payment).where(Payment.gateway_payment_id == transaction_id)
                )
                payment = result.scalar_one_or_none()
                
                if payment:
                    # Update payment status
                    new_status = PaymentStatus.SUCCESS if status == 'success' else PaymentStatus.FAILED
                    await db.execute(
                        update(Payment)
                        .where(Payment.id == payment.id)
                        .values(
                            status=new_status,
                            gateway_response=payload,
                            completed_at=datetime.utcnow() if new_status == PaymentStatus.SUCCESS else None,
                            failure_reason=payload.get('error_message') if new_status == PaymentStatus.FAILED else None
                        )
                    )
                    await db.commit()
                    
                    logger.info(f"Orange Money payment updated: {payment.id} -> {new_status}")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Orange Money webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook processing failed"
        )


@router.post("/webhooks/mtn-money")
async def mtn_money_webhook(request: Request):
    """
    Handle MTN Mobile Money webhooks.
    """
    try:
        payload = await request.json()
        
        # Process MTN Mobile Money webhook
        reference_id = payload.get('referenceId')
        status = payload.get('status')
        
        if reference_id and status:
            async with get_db_context() as db:
                # Find payment by gateway payment ID
                result = await db.execute(
                    select(Payment).where(Payment.gateway_payment_id == reference_id)
                )
                payment = result.scalar_one_or_none()
                
                if payment:
                    # Update payment status
                    new_status = PaymentStatus.SUCCESS if status == 'SUCCESSFUL' else PaymentStatus.FAILED
                    await db.execute(
                        update(Payment)
                        .where(Payment.id == payment.id)
                        .values(
                            status=new_status,
                            gateway_response=payload,
                            completed_at=datetime.utcnow() if new_status == PaymentStatus.SUCCESS else None,
                            failure_reason=payload.get('reason') if new_status == PaymentStatus.FAILED else None
                        )
                    )
                    await db.commit()
                    
                    logger.info(f"MTN Money payment updated: {payment.id} -> {new_status}")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"MTN Money webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook processing failed"
        )


# Admin endpoints
@router.post("/refund", response_model=PaymentRefundResponse)
async def create_payment_refund(
    refund_request: PaymentRefundCreate,
    admin_user: object = Depends(get_current_admin_user)
):
    """
    Create a refund for a payment (admin only).
    """
    try:
        result = await create_refund(
            payment_id=refund_request.payment_id,
            amount=refund_request.amount,
            reason=refund_request.reason
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error_message or "Refund processing failed"
            )
        
        return PaymentRefundResponse(
            refund_id=result.transaction_id,
            payment_id=refund_request.payment_id,
            amount=refund_request.amount,
            status=result.status.value,
            reason=refund_request.reason
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refund creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Refund creation failed"
        )


@router.get("/admin/payments", response_model=PaginatedResponse[PaymentResponse])
async def get_all_payments(
    page: int = 1,
    per_page: int = 20,
    status: Optional[str] = None,
    gateway: Optional[str] = None,
    admin_user: object = Depends(get_current_admin_user)
):
    """
    Get all payments (admin only).
    """
    try:
        async with get_db_context() as db:
            query = select(Payment)
            
            if status:
                query = query.where(Payment.status == status)
            
            if gateway:
                query = query.where(Payment.gateway == gateway)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = await db.execute(count_query)
            total = total.scalar()
            
            # Get paginated results
            payments = await db.execute(
                query.options(selectinload(Payment.order))
                .order_by(Payment.created_at.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
            payments = payments.scalars().all()
            
            return PaginatedResponse(
                items=[PaymentResponse.from_orm(payment) for payment in payments],
                total=total,
                page=page,
                per_page=per_page,
                pages=(total + per_page - 1) // per_page
            )
            
    except Exception as e:
        logger.error(f"Failed to get payments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payments"
        )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    current_user: object = Depends(get_current_user)
):
    """Get payment details by ID."""
    try:
        async with get_db_context() as db:
            # Get payment and verify user ownership through order
            payment = await db.execute(
                select(Payment)
                .join(Order)
                .where(
                    Payment.id == payment_id,
                    Order.user_id == current_user.id
                )
                .options(selectinload(Payment.refunds))
            )
            payment = payment.scalar_one_or_none()
            
            if not payment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found"
                )
            
            return payment
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment"
        )


@router.post("/", response_model=PaymentIntentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreateRequest,
    current_user: object = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Create a new payment for an order.
    
    - **order_id**: Order to pay for
    - **gateway**: Payment gateway (stripe, orange_money, mtn_mobile_money)
    - **amount**: Payment amount
    - **customer_phone**: Phone number (required for mobile money)
    - **customer_email**: Email (for Stripe)
    """
    try:
        async with get_db_context() as db:
            # Verify order exists and belongs to user
            order = await db.execute(
                select(Order).where(
                    Order.id == payment_data.order_id,
                    Order.user_id == current_user.id
                )
            )
            order = order.scalar_one_or_none()
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            # Check if order can accept payments
            if order.status in ['cancelled', 'refunded', 'completed']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Order cannot accept new payments"
                )
            
            # Validate payment amount
            remaining_balance = order.get_remaining_balance()
            if payment_data.amount > remaining_balance:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Payment amount exceeds remaining balance: {remaining_balance} XAF"
                )
            
            # Create payment record
            payment = Payment(
                order_id=payment_data.order_id,
                gateway=payment_data.gateway,
                amount=payment_data.amount,
                currency=payment_data.currency,
                customer_phone=payment_data.customer_phone,
                customer_email=payment_data.customer_email or current_user.email
            )
            
            payment.generate_reference_id()
            db.add(payment)
            await db.commit()
            await db.refresh(payment)
            
            # Process payment based on gateway
            payment_intent = await process_payment_gateway(
                payment, payment_data.gateway, background_tasks
            )
            
            logger.info(f"Payment created: {payment.reference_id} for order {order.order_number}")
            
            return payment_intent
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment"
        )


@router.post("/{payment_id}/confirm", response_model=BaseResponse)
async def confirm_payment(
    payment_id: str,
    current_user: object = Depends(get_current_user),
    confirmation_data: dict = {}
):
    """
    Confirm payment (for certain gateways that require confirmation).
    
    Used for mobile money payments where user needs to confirm on their device.
    """
    try:
        async with get_db_context() as db:
            # Get payment and verify ownership
            payment = await db.execute(
                select(Payment)
                .join(Order)
                .where(
                    Payment.id == payment_id,
                    Order.user_id == current_user.id
                )
            )
            payment = payment.scalar_one_or_none()
            
            if not payment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found"
                )
            
            if payment.status != 'pending':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment is not in pending state"
                )
            
            # Process confirmation based on gateway
            success = await confirm_payment_gateway(payment, confirmation_data)
            
            if success:
                payment.update_status('success')
                await update_order_payment_status(db, payment.order_id)
                await db.commit()
                
                logger.info(f"Payment confirmed: {payment.reference_id}")
                return BaseResponse(message="Payment confirmed successfully")
            else:
                payment.update_status('failed', failure_reason="Confirmation failed")
                await db.commit()
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment confirmation failed"
                )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to confirm payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm payment"
        )


# Webhook endpoints
@router.post("/webhooks/{gateway}")
async def payment_webhook(
    gateway: str,
    request: Request,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Handle payment webhooks from gateways.
    
    This endpoint receives notifications from payment providers about payment status changes.
    """
    try:
        # Get raw body and headers
        body = await request.body()
        headers = dict(request.headers)
        
        # Parse webhook payload
        try:
            import json
            payload = json.loads(body.decode())
        except:
            payload = {"raw_body": body.decode()}
        
        async with get_db_context() as db:
            # Store webhook for processing
            webhook = PaymentWebhook(
                gateway=gateway,
                event_type=payload.get('event_type', 'unknown'),
                webhook_id=payload.get('id', payload.get('webhook_id')),
                payload=payload,
                headers=headers
            )
            
            db.add(webhook)
            await db.commit()
            await db.refresh(webhook)
        
        # Process webhook in background
        background_tasks.add_task(process_webhook, webhook.id)
        
        logger.info(f"Webhook received from {gateway}: {webhook.event_type}")
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


# Admin endpoints
@router.get("/admin/payments", response_model=PaginatedResponse[PaymentResponse])
async def list_all_payments(
    admin_user: object = Depends(get_current_admin_user),
    pagination: dict = Depends(get_pagination_params),
    gateway: Optional[PaymentGateway] = None,
    status: Optional[PaymentStatus] = None,
    order_id: Optional[str] = None
):
    """List all payments (admin only)."""
    try:
        async with get_db_context() as db:
            # Build query
            query = select(Payment).options(selectinload(Payment.order))
            
            # Apply filters
            if gateway:
                query = query.where(Payment.gateway == gateway)
            
            if status:
                query = query.where(Payment.status == status)
            
            if order_id:
                query = query.where(Payment.order_id == order_id)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = await db.execute(count_query)
            total = total.scalar()
            
            # Get paginated results
            payments = await db.execute(
                query.order_by(Payment.created_at.desc())
                .offset(pagination['offset'])
                .limit(pagination['per_page'])
            )
            
            return PaginatedResponse.create(
                items=payments.scalars().all(),
                page=pagination['page'],
                per_page=pagination['per_page'],
                total=total
            )
            
    except Exception as e:
        logger.error(f"Failed to list payments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payments"
        )


@router.post("/admin/payments/{payment_id}/refund", response_model=PaymentRefundResponse)
async def create_refund(
    payment_id: str,
    refund_data: PaymentRefundCreate,
    admin_user: object = Depends(get_current_admin_user)
):
    """Create payment refund (admin only)."""
    try:
        async with get_db_context() as db:
            # Get payment
            payment = await db.execute(
                select(Payment).where(Payment.id == payment_id)
            )
            payment = payment.scalar_one_or_none()
            
            if not payment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found"
                )
            
            if not payment.can_be_refunded:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment cannot be refunded"
                )
            
            # Validate refund amount
            if refund_data.amount > payment.remaining_refundable:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Refund amount exceeds refundable amount: {payment.remaining_refundable} XAF"
                )
            
            # Create refund
            refund = PaymentRefund(
                payment_id=payment_id,
                amount=refund_data.amount,
                reason=refund_data.reason,
                notes=refund_data.notes,
                processed_by_id=admin_user.id
            )
            
            db.add(refund)
            await db.commit()
            await db.refresh(refund)
            
            # Process refund through gateway (background task)
            # This would integrate with actual payment gateways
            refund.status = 'success'  # Simplified for demo
            refund.processed_at = datetime.utcnow()
            
            # Update payment status if fully refunded
            if payment.total_refunded + refund_data.amount >= payment.amount:
                payment.status = 'refunded'
            
            await db.commit()
            
            logger.info(f"Refund created: {refund_data.amount} XAF for payment {payment.reference_id}")
            
            return PaymentRefundResponse(
                **refund.__dict__,
                processed_by_name=f"{admin_user.first_name} {admin_user.last_name}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create refund: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create refund"
        )


# Helper functions
async def process_payment_gateway(
    payment: Payment, 
    gateway: PaymentGateway, 
    background_tasks: BackgroundTasks
) -> PaymentIntentResponse:
    """Process payment through specified gateway."""
    
    if gateway == PaymentGateway.STRIPE:
        return await process_stripe_payment(payment)
    elif gateway == PaymentGateway.ORANGE_MONEY:
        return await process_orange_money_payment(payment)
    elif gateway == PaymentGateway.MTN_MOBILE_MONEY:
        return await process_mtn_momo_payment(payment)
    elif gateway == PaymentGateway.CASH_ON_DELIVERY:
        return await process_cash_on_delivery(payment)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported payment gateway: {gateway}"
        )


async def process_stripe_payment(payment: Payment) -> PaymentIntentResponse:
    """Process Stripe payment."""
    # This would integrate with Stripe API
    # For demo purposes, return mock payment intent
    
    return PaymentIntentResponse(
        payment_id=str(payment.id),
        client_secret="pi_mock_client_secret",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        instructions="Complete payment using Stripe checkout"
    )


async def process_orange_money_payment(payment: Payment) -> PaymentIntentResponse:
    """Process Orange Money payment."""
    # This would integrate with Orange Money API
    
    if not payment.customer_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number required for Orange Money payment"
        )
    
    return PaymentIntentResponse(
        payment_id=str(payment.id),
        redirect_url=f"https://api.orange.com/orange-money-webpay/cm/v1/webpayment?token=mock_token",
        instructions=f"Complete payment on your Orange Money account ({payment.customer_phone})",
        expires_at=datetime.utcnow() + timedelta(minutes=15)
    )


async def process_mtn_momo_payment(payment: Payment) -> PaymentIntentResponse:
    """Process MTN Mobile Money payment."""
    # This would integrate with MTN Mobile Money API
    
    if not payment.customer_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number required for MTN Mobile Money payment"
        )
    
    return PaymentIntentResponse(
        payment_id=str(payment.id),
        instructions=f"You will receive an MTN Mobile Money prompt on {payment.customer_phone}. Enter your PIN to complete the payment.",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )


async def process_cash_on_delivery(payment: Payment) -> PaymentIntentResponse:
    """Process Cash on Delivery."""
    # Update payment status to pending (will be confirmed on delivery)
    payment.update_status('pending', gateway_response={"method": "cash_on_delivery"})
    
    return PaymentIntentResponse(
        payment_id=str(payment.id),
        instructions="Payment will be collected upon delivery. Please prepare the exact amount.",
        expires_at=datetime.utcnow() + timedelta(days=7)
    )


async def confirm_payment_gateway(payment: Payment, confirmation_data: dict) -> bool:
    """Confirm payment through gateway."""
    # This would implement gateway-specific confirmation logic
    # For demo, return True for mobile money payments
    
    if payment.gateway in [PaymentGateway.ORANGE_MONEY, PaymentGateway.MTN_MOBILE_MONEY]:
        # In real implementation, this would verify with the gateway
        return True
    
    return False


async def update_order_payment_status(db: AsyncSession, order_id: str):
    """Update order status based on payment status."""
    # Get order and its payments
    order = await db.execute(
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.payments))
    )
    order = order.scalar_one()
    
    total_paid = order.get_total_paid()
    
    if total_paid >= order.deposit_amount and order.status == 'pending':
        # Minimum deposit paid
        order.change_status('partially_paid', f"Deposit paid: {total_paid} XAF")
    elif total_paid >= order.total_amount:
        # Fully paid
        order.change_status('paid_full', f"Order fully paid: {total_paid} XAF")


async def process_webhook(webhook_id: str):
    """Process payment webhook in background."""
    try:
        async with get_db_context() as db:
            webhook = await db.get(PaymentWebhook, webhook_id)
            if not webhook:
                return
            
            # Process webhook based on gateway
            if webhook.gateway == 'stripe':
                await process_stripe_webhook(db, webhook)
            elif webhook.gateway == 'orange_money':
                await process_orange_money_webhook(db, webhook)
            elif webhook.gateway == 'mtn_mobile_money':
                await process_mtn_momo_webhook(db, webhook)
            
            # Mark webhook as processed
            webhook.mark_as_processed()
            await db.commit()
            
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        # Mark webhook as failed
        async with get_db_context() as db:
            webhook = await db.get(PaymentWebhook, webhook_id)
            if webhook:
                webhook.mark_as_processed(str(e))
                await db.commit()


async def process_stripe_webhook(db: AsyncSession, webhook: PaymentWebhook):
    """Process Stripe webhook."""
    # This would implement Stripe webhook processing
    pass


async def process_orange_money_webhook(db: AsyncSession, webhook: PaymentWebhook):
    """Process Orange Money webhook."""
    # This would implement Orange Money webhook processing
    pass


async def process_mtn_momo_webhook(db: AsyncSession, webhook: PaymentWebhook):
    """Process MTN Mobile Money webhook."""
    # This would implement MTN MoMo webhook processing
    pass


# Import required modules
from datetime import datetime, timedelta
