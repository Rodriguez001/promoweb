"""
Order and Payment schemas for PromoWeb Africa.
Pydantic models for order and payment data validation.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from pydantic import BaseModel, Field, validator, EmailStr
from decimal import Decimal
from enum import Enum

# Import pour éviter les erreurs de référence circulaire
if TYPE_CHECKING:
    from app.schemas.payment import PaymentResponse
    from app.schemas.shipping import ShippingResponse


# Enums
class OrderStatus(str, Enum):
    """Order status options."""
    PENDING = "pending"
    PARTIALLY_PAID = "partially_paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    DELIVERY_FAILED = "delivery_failed"
    PAID_FULL = "paid_full"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Payment status options."""
    INITIATED = "initiated"
    PROCESSING = "processing"
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    EXPIRED = "expired"
    REFUNDED = "refunded"


class PaymentGateway(str, Enum):
    """Payment gateway options."""
    STRIPE = "stripe"
    ORANGE_MONEY = "orange_money"
    MTN_MOBILE_MONEY = "mtn_mobile_money"
    CASH_ON_DELIVERY = "cash_on_delivery"


# Order item schemas
class OrderItemBase(BaseModel):
    """Base order item schema."""
    product_id: str
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)


class OrderItemCreate(OrderItemBase):
    """Schema for creating order item."""
    pass


class OrderItemResponse(OrderItemBase):
    """Schema for order item response."""
    id: str
    order_id: str
    total_price: Decimal
    product_title: str
    product_image: Optional[str]
    product_snapshot: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


# Address schemas for orders
class OrderAddressBase(BaseModel):
    """Base order address schema."""
    name: str = Field(..., min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    country: str = Field(default="CM", max_length=2)


class OrderAddressCreate(OrderAddressBase):
    """Schema for creating order address."""
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


# Order schemas
class OrderBase(BaseModel):
    """Base order schema."""
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    """Schema for creating order."""
    items: List[OrderItemCreate] = Field(..., min_items=1)
    billing_address: OrderAddressCreate
    shipping_address: Optional[OrderAddressCreate] = None  # If None, use billing address
    shipping_address_id: Optional[str] = None  # Use saved address
    billing_address_id: Optional[str] = None   # Use saved address


class OrderUpdate(BaseModel):
    """Schema for updating order."""
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None
    admin_notes: Optional[str] = None


class OrderResponse(OrderBase):
    """Schema for order response."""
    id: str
    order_number: str
    user_id: str
    status: OrderStatus
    total_amount: Decimal
    deposit_amount: Decimal
    remaining_amount: Decimal
    shipping_cost: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    
    # Addresses
    billing_name: Optional[str]
    billing_email: Optional[str]
    billing_phone: Optional[str]
    billing_address_full: str
    shipping_name: Optional[str]
    shipping_address_full: str
    
    # Status info
    is_paid_in_full: bool
    is_partially_paid: bool
    can_be_cancelled: bool
    payment_progress: float
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    delivered_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class OrderDetail(OrderResponse):
    """Detailed order information."""
    items: List[OrderItemResponse] = []
    payments: List[Dict[str, Any]] = []  # Simplified to avoid circular imports
    shipping: Optional[Dict[str, Any]] = None  # Simplified to avoid circular imports
    status_history: List["OrderStatusHistoryResponse"] = []
    user_name: str
    user_email: str


class OrderListResponse(BaseModel):
    """Paginated order list response."""
    items: List[OrderResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


# Order status history schemas
class OrderStatusHistoryResponse(BaseModel):
    """Order status history response."""
    id: str
    previous_status: Optional[OrderStatus]
    new_status: OrderStatus
    notes: Optional[str]
    changed_by_name: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Payment schemas
class PaymentBase(BaseModel):
    """Base payment schema."""
    gateway: PaymentGateway
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="XAF", max_length=3)
    customer_phone: Optional[str] = Field(None, max_length=20)
    customer_email: Optional[EmailStr] = None


class PaymentCreate(PaymentBase):
    """Schema for creating payment."""
    order_id: str


class PaymentResponse(PaymentBase):
    """Schema for payment response."""
    id: str
    order_id: str
    transaction_id: Optional[str]
    reference_id: Optional[str]
    status: PaymentStatus
    gateway_transaction_id: Optional[str]
    failure_reason: Optional[str]
    retry_count: int
    
    # Status checks
    is_successful: bool
    is_pending: bool
    is_failed: bool
    can_be_refunded: bool
    total_refunded: Decimal
    remaining_refundable: Decimal
    
    # Timestamps
    initiated_at: datetime
    processed_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PaymentIntent(BaseModel):
    """Payment intent for client-side processing."""
    payment_id: str
    client_secret: Optional[str]  # For Stripe
    redirect_url: Optional[str]   # For mobile money
    qr_code: Optional[str]        # For mobile money QR codes
    instructions: Optional[str]   # Payment instructions
    expires_at: datetime


# Payment refund schemas
class PaymentRefundCreate(BaseModel):
    """Schema for creating payment refund."""
    amount: Decimal = Field(..., gt=0)
    reason: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class PaymentRefundResponse(BaseModel):
    """Schema for payment refund response."""
    id: str
    payment_id: str
    amount: Decimal
    reason: Optional[str]
    notes: Optional[str]
    status: PaymentStatus
    gateway_refund_id: Optional[str]
    failure_reason: Optional[str]
    processed_by_name: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Cart to order conversion
class CartCheckout(BaseModel):
    """Schema for converting cart to order."""
    cart_id: str
    billing_address: OrderAddressCreate
    shipping_address: Optional[OrderAddressCreate] = None
    shipping_address_id: Optional[str] = None
    billing_address_id: Optional[str] = None
    notes: Optional[str] = None
    payment_gateway: PaymentGateway


# Order analytics schemas
class OrderAnalytics(BaseModel):
    """Order analytics data."""
    total_orders: int
    total_revenue: Decimal
    average_order_value: Decimal
    conversion_rate: float
    orders_by_status: Dict[str, int]
    orders_by_payment_method: Dict[str, int]
    top_products: List[Dict[str, Any]]
    period_start: datetime
    period_end: datetime


class OrderReportFilters(BaseModel):
    """Filters for order reports."""
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    status: Optional[List[OrderStatus]] = None
    payment_gateway: Optional[List[PaymentGateway]] = None
    user_id: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None


# Order search and filtering
class OrderSearchQuery(BaseModel):
    """Order search query parameters."""
    q: Optional[str] = Field(None, description="Search by order number, customer name, or email")
    status: Optional[List[OrderStatus]] = Field(None, description="Filter by status")
    payment_gateway: Optional[List[PaymentGateway]] = Field(None, description="Filter by payment method")
    date_from: Optional[date] = Field(None, description="Orders from date")
    date_to: Optional[date] = Field(None, description="Orders to date")
    min_amount: Optional[Decimal] = Field(None, ge=0, description="Minimum order amount")
    max_amount: Optional[Decimal] = Field(None, ge=0, description="Maximum order amount")
    user_id: Optional[str] = Field(None, description="Filter by user")
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", pattern=r"^(asc|desc)$", description="Sort order")


# Bulk operations
class OrderBulkStatusUpdate(BaseModel):
    """Schema for bulk order status updates."""
    order_ids: List[str] = Field(..., min_items=1)
    status: OrderStatus
    notes: Optional[str] = None


class OrderExport(BaseModel):
    """Schema for order export configuration."""
    format: str = Field(default="csv", pattern=r"^(csv|xlsx|json)$")
    filters: OrderReportFilters
    include_items: bool = Field(default=True)
    include_payments: bool = Field(default=True)
    include_shipping: bool = Field(default=False)


# Forward references - Removed model_rebuild() to avoid circular import issues
# OrderDetail.model_rebuild()
