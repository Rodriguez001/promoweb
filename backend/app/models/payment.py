"""
Payment models for PromoWeb Africa.
Handles multi-gateway payments including Stripe, Orange Money, and MTN Mobile Money.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Numeric, Text, Index
)
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSON
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


# Payment status enum
payment_status_enum = ENUM(
    'initiated', 'processing', 'pending', 'success', 
    'failed', 'expired', 'refunded',
    name='payment_status',
    create_type=False
)

# Payment gateway enum
payment_gateway_enum = ENUM(
    'stripe', 'orange_money', 'mtn_mobile_money', 'cash_on_delivery',
    name='payment_gateway',
    create_type=False
)


class Payment(Base):
    """Payment model supporting multiple gateways and partial payments."""
    
    __tablename__ = "payments"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    
    # Payment identification
    transaction_id = Column(String(255), unique=True, nullable=True, index=True)
    reference_id = Column(String(255), nullable=True, index=True)  # Internal reference
    
    # Payment details
    gateway = Column(payment_gateway_enum, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default='XAF', nullable=False)
    
    # Payment status
    status = Column(payment_status_enum, default='initiated', nullable=False, index=True)
    
    # Gateway response data
    gateway_response = Column(JSON, nullable=True)
    gateway_transaction_id = Column(String(255), nullable=True, index=True)
    
    # Error handling
    failure_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Customer information
    customer_phone = Column(String(20), nullable=True)  # For mobile money
    customer_email = Column(String(255), nullable=True)  # For Stripe
    
    # Timestamps
    initiated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="payments")
    refunds = relationship("PaymentRefund", back_populates="payment")
    
    # Indexes
    __table_args__ = (
        Index('idx_payment_order_status', 'order_id', 'status'),
        Index('idx_payment_gateway_status', 'gateway', 'status'),
        Index('idx_payment_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Payment(id={self.id}, gateway='{self.gateway}', amount={self.amount}, status='{self.status}')>"
    
    @validates('amount')
    def validate_amount(self, key, value):
        """Validate amount is positive."""
        if value <= 0:
            raise ValueError("Payment amount must be positive")
        return value
    
    @property
    def is_successful(self) -> bool:
        """Check if payment is successful."""
        return self.status == 'success'
    
    @property
    def is_pending(self) -> bool:
        """Check if payment is pending."""
        return self.status in ['initiated', 'processing', 'pending']
    
    @property
    def is_failed(self) -> bool:
        """Check if payment failed."""
        return self.status in ['failed', 'expired']
    
    @property
    def is_refunded(self) -> bool:
        """Check if payment is refunded."""
        return self.status == 'refunded'
    
    @property
    def can_be_refunded(self) -> bool:
        """Check if payment can be refunded."""
        return self.status == 'success' and self.gateway != 'cash_on_delivery'
    
    @property
    def is_expired(self) -> bool:
        """Check if payment is expired."""
        return self.expires_at and datetime.utcnow() > self.expires_at
    
    @property
    def total_refunded(self) -> Decimal:
        """Get total refunded amount."""
        return sum(r.amount for r in self.refunds if r.status == 'success')
    
    @property
    def remaining_refundable(self) -> Decimal:
        """Get remaining refundable amount."""
        return self.amount - self.total_refunded
    
    def update_status(self, status: str, gateway_response: Dict = None, 
                     gateway_transaction_id: str = None, failure_reason: str = None) -> None:
        """Update payment status with additional information."""
        self.status = status
        self.updated_at = datetime.utcnow()
        
        if status == 'success':
            self.processed_at = datetime.utcnow()
        
        if gateway_response:
            self.gateway_response = gateway_response
        
        if gateway_transaction_id:
            self.gateway_transaction_id = gateway_transaction_id
        
        if failure_reason:
            self.failure_reason = failure_reason
    
    def generate_reference_id(self) -> str:
        """Generate internal reference ID."""
        if not self.reference_id:
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            self.reference_id = f"PAY_{timestamp}_{str(self.id)[-8:]}"
        return self.reference_id
    
    def can_retry(self, max_retries: int = 3) -> bool:
        """Check if payment can be retried."""
        return self.retry_count < max_retries and self.status in ['failed', 'expired']
    
    def increment_retry_count(self) -> None:
        """Increment retry count."""
        self.retry_count += 1
        self.updated_at = datetime.utcnow()


class PaymentRefund(Base):
    """Payment refund model."""
    
    __tablename__ = "payment_refunds"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    
    # Refund details
    amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Status
    status = Column(payment_status_enum, default='initiated', nullable=False)
    
    # Gateway information
    gateway_refund_id = Column(String(255), nullable=True)
    gateway_response = Column(JSON, nullable=True)
    
    # Error handling
    failure_reason = Column(Text, nullable=True)
    
    # Admin who processed the refund
    processed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    payment = relationship("Payment", back_populates="refunds")
    processed_by = relationship("User")
    
    def __repr__(self):
        return f"<PaymentRefund(id={self.id}, payment_id={self.payment_id}, amount={self.amount})>"
    
    @validates('amount')
    def validate_amount(self, key, value):
        """Validate refund amount."""
        if value <= 0:
            raise ValueError("Refund amount must be positive")
        return value


class PaymentWebhook(Base):
    """Webhook events from payment gateways."""
    
    __tablename__ = "payment_webhooks"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Webhook details
    gateway = Column(payment_gateway_enum, nullable=False)
    event_type = Column(String(100), nullable=False)
    webhook_id = Column(String(255), nullable=True)  # Gateway webhook ID
    
    # Related payment (if identifiable)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=True)
    
    # Webhook data
    payload = Column(JSON, nullable=False)  # Raw webhook payload
    headers = Column(JSON, nullable=True)   # Request headers
    
    # Processing status
    processed = Column(Boolean, default=False, nullable=False)
    processing_error = Column(Text, nullable=True)
    
    # Verification
    signature_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship
    payment = relationship("Payment")
    
    # Indexes
    __table_args__ = (
        Index('idx_webhook_gateway_type', 'gateway', 'event_type'),
        Index('idx_webhook_processed', 'processed'),
        Index('idx_webhook_received_at', 'received_at'),
    )
    
    def __repr__(self):
        return f"<PaymentWebhook(id={self.id}, gateway='{self.gateway}', event='{self.event_type}')>"
    
    def mark_as_processed(self, error: str = None) -> None:
        """Mark webhook as processed."""
        self.processed = True
        self.processed_at = datetime.utcnow()
        if error:
            self.processing_error = error


class PaymentMethod(Base):
    """Saved payment methods for users."""
    
    __tablename__ = "payment_methods"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Payment method details
    gateway = Column(payment_gateway_enum, nullable=False)
    method_type = Column(String(50), nullable=False)  # 'card', 'mobile_money', etc.
    
    # Tokenized information (never store actual card numbers)
    gateway_method_id = Column(String(255), nullable=True)  # Stripe payment method ID
    last_four = Column(String(4), nullable=True)  # Last 4 digits for cards
    brand = Column(String(50), nullable=True)  # Visa, Mastercard, etc.
    
    # Mobile money information
    phone_number = Column(String(20), nullable=True)  # For mobile money (masked)
    network = Column(String(50), nullable=True)  # Orange, MTN, etc.
    
    # Display information
    display_name = Column(String(100), nullable=True)  # User-friendly name
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_payment_method_user_default', 'user_id', 'is_default'),
        Index('idx_payment_method_gateway_type', 'gateway', 'method_type'),
    )
    
    def __repr__(self):
        return f"<PaymentMethod(id={self.id}, user_id={self.user_id}, gateway='{self.gateway}')>"
    
    @property
    def masked_display(self) -> str:
        """Get masked display string for the payment method."""
        if self.method_type == 'card' and self.last_four:
            brand = self.brand or 'Card'
            return f"{brand} ending in {self.last_four}"
        elif self.method_type == 'mobile_money' and self.phone_number:
            # Mask phone number: +237XXXXXX1234 -> +237****1234
            phone = self.phone_number
            if len(phone) > 4:
                masked = phone[:-4].replace(phone[4:-4], '*' * len(phone[4:-4]))
                return f"{self.network} {masked}{phone[-4:]}"
            return f"{self.network} {phone}"
        
        return self.display_name or f"{self.gateway} {self.method_type}"
    
    def update_last_used(self) -> None:
        """Update last used timestamp."""
        self.last_used_at = datetime.utcnow()


class PaymentTransaction(Base):
    """Detailed transaction log for accounting and reconciliation."""
    
    __tablename__ = "payment_transactions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Related payment
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=True)
    refund_id = Column(UUID(as_uuid=True), ForeignKey("payment_refunds.id"), nullable=True)
    
    # Transaction details
    transaction_type = Column(String(20), nullable=False)  # 'payment', 'refund', 'fee'
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default='XAF', nullable=False)
    
    # Gateway fees
    gateway_fee = Column(Numeric(10, 2), default=0, nullable=False)
    net_amount = Column(Numeric(10, 2), nullable=False)  # Amount after fees
    
    # Settlement information
    settled = Column(Boolean, default=False, nullable=False)
    settlement_date = Column(DateTime(timezone=True), nullable=True)
    settlement_reference = Column(String(255), nullable=True)
    
    # Accounting
    accounting_reference = Column(String(255), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    payment = relationship("Payment")
    refund = relationship("PaymentRefund")
    
    def __repr__(self):
        return f"<PaymentTransaction(id={self.id}, type='{self.transaction_type}', amount={self.amount})>"


class ExchangeRate(Base):
    """Exchange rate model for currency conversions."""
    
    __tablename__ = "exchange_rates"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Currency pair
    from_currency = Column(String(3), nullable=False)  # EUR
    to_currency = Column(String(3), nullable=False)    # XAF
    
    # Rate information
    rate = Column(Numeric(precision=12, scale=6), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    source = Column(String(50), nullable=False)  # api, manual, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_exchange_rate_currencies_date', 'from_currency', 'to_currency', 'date'),
    )
    
    def __repr__(self):
        return f"<ExchangeRate({self.from_currency}->{self.to_currency}: {self.rate})>"
