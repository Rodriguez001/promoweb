"""
Payment schemas for PromoWeb Africa.
Pydantic models for payment-related API requests and responses.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.schemas.common import BaseResponse


class PaymentGateway(str, Enum):
    """Payment gateway options."""
    STRIPE = "stripe"
    ORANGE_MONEY = "orange_money"
    MTN_MOBILE_MONEY = "mtn_mobile_money"
    CASH_ON_DELIVERY = "cash_on_delivery"


class PaymentStatus(str, Enum):
    """Payment status options."""
    INITIATED = "initiated"
    PROCESSING = "processing"
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    EXPIRED = "expired"
    REFUNDED = "refunded"


class PaymentCreateRequest(BaseModel):
    """Request to create a payment."""
    order_id: str = Field(..., description="Order ID to pay for")
    gateway: PaymentGateway = Field(..., description="Payment gateway to use")
    is_partial: bool = Field(False, description="Whether this is a partial payment (30% down)")
    return_url: Optional[str] = Field(None, description="URL to redirect after payment")
    
    class Config:
        use_enum_values = True


class PaymentIntentResponse(BaseModel):
    """Response when creating a payment intent."""
    payment_id: str
    status: str
    gateway: str
    amount: Decimal
    currency: str
    gateway_response: Optional[Dict[str, Any]] = None
    requires_action: bool = False
    redirect_url: Optional[str] = None
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class PaymentResponse(BaseModel):
    """Payment response model."""
    id: str
    order_id: str
    gateway: str
    amount: Decimal
    currency: str
    status: str
    transaction_id: Optional[str] = None
    gateway_payment_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class PaymentStatusResponse(BaseModel):
    """Payment status response."""
    payment_id: str
    status: str
    gateway: str
    amount: Decimal
    currency: str
    transaction_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class PartialPaymentCalculation(BaseModel):
    """Partial payment calculation response."""
    order_id: str
    total_amount: Decimal
    down_payment: Decimal
    remaining_balance: Decimal
    down_payment_percentage: Decimal
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class PaymentRefundCreate(BaseModel):
    """Request to create a refund."""
    payment_id: str = Field(..., description="Payment ID to refund")
    amount: Optional[Decimal] = Field(None, description="Amount to refund (full refund if not specified)")
    reason: str = Field(..., description="Reason for refund")
    
    @validator('amount')
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Refund amount must be positive')
        return v


class PaymentRefundResponse(BaseModel):
    """Payment refund response."""
    refund_id: str
    payment_id: str
    amount: Decimal
    status: str
    reason: str
    created_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class PaymentMethodCreate(BaseModel):
    """Request to save a payment method."""
    user_id: str
    gateway: PaymentGateway
    gateway_method_id: str
    method_type: str  # card, mobile_money, bank_account
    last_four_digits: Optional[str] = None
    brand: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    is_default: bool = False


class PaymentMethodResponse(BaseModel):
    """Payment method response."""
    id: str
    gateway: str
    method_type: str
    last_four_digits: Optional[str] = None
    brand: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    is_default: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentAnalytics(BaseModel):
    """Payment analytics response."""
    total_payments: int
    successful_payments: int
    failed_payments: int
    total_amount: Decimal
    average_amount: Decimal
    success_rate: float
    gateway_breakdown: Dict[str, Dict[str, Any]]
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class WebhookEvent(BaseModel):
    """Webhook event model."""
    event_type: str
    gateway: str
    payment_id: Optional[str] = None
    transaction_id: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[Decimal] = None
    data: Dict[str, Any]
    received_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class PaymentReceiptData(BaseModel):
    """Data for payment receipt generation."""
    payment_id: str
    order_number: str
    customer_name: str
    customer_email: str
    amount: Decimal
    currency: str
    payment_date: datetime
    gateway: str
    transaction_id: str
    items: List[Dict[str, Any]]
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class MobileMoneyPaymentRequest(BaseModel):
    """Mobile money specific payment request."""
    phone_number: str = Field(..., description="Customer phone number")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    currency: str = Field(default="XAF", description="Currency code")
    reference: str = Field(..., description="Payment reference")
    description: Optional[str] = Field(None, description="Payment description")
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Basic validation for Cameroon phone numbers
        if not v.startswith('+237') and not v.startswith('237') and not v.startswith('6') and not v.startswith('2'):
            raise ValueError('Invalid Cameroon phone number format')
        return v


class StripePaymentRequest(BaseModel):
    """Stripe specific payment request."""
    amount: Decimal = Field(..., gt=0, description="Payment amount in XAF")
    currency: str = Field(default="XAF", description="Currency code")
    customer_email: Optional[str] = Field(None, description="Customer email")
    payment_method_types: List[str] = Field(default=["card"], description="Allowed payment method types")
    metadata: Optional[Dict[str, str]] = Field(None, description="Additional metadata")


class PaymentSummary(BaseModel):
    """Payment summary for dashboard."""
    period: str  # daily, weekly, monthly
    total_amount: Decimal
    transaction_count: int
    success_rate: float
    top_gateway: str
    average_transaction_amount: Decimal
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }
