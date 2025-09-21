"""
Cart schemas for PromoWeb Africa.
Pydantic models for shopping cart data validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from decimal import Decimal


# Cart item schemas
class CartItemBase(BaseModel):
    """Base cart item schema."""
    product_id: str
    quantity: int = Field(..., gt=0, description="Item quantity")


class CartItemCreate(CartItemBase):
    """Schema for adding item to cart."""
    notes: Optional[str] = Field(None, max_length=500, description="Special notes or instructions")


class CartItemUpdate(BaseModel):
    """Schema for updating cart item."""
    quantity: int = Field(..., gt=0, description="New quantity")
    notes: Optional[str] = Field(None, max_length=500, description="Special notes or instructions")


class CartItemResponse(CartItemBase):
    """Schema for cart item response."""
    id: str
    cart_id: str
    unit_price: Decimal
    total_price: Decimal
    current_price: Decimal  # Price with current promotions
    savings: Decimal        # Amount saved from promotions
    notes: Optional[str]
    
    # Product info
    product_title: str
    product_image: Optional[str]
    product_brand: Optional[str]
    product_weight_kg: Optional[Decimal]
    
    # Availability
    is_available: bool
    availability_message: Optional[str]
    max_available_quantity: int
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Cart schemas
class CartBase(BaseModel):
    """Base cart schema."""
    pass


class CartResponse(CartBase):
    """Schema for cart response."""
    id: str
    user_id: Optional[str]
    session_id: Optional[str]
    total_amount: Decimal
    total_items: int
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CartDetail(CartResponse):
    """Detailed cart with items and totals."""
    items: List[CartItemResponse] = []
    totals: "CartTotals"
    is_expired: bool
    is_empty: bool


class CartTotals(BaseModel):
    """Cart totals breakdown."""
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    shipping_estimate: Decimal
    total: Decimal
    item_count: int
    total_weight: Decimal
    savings_amount: Decimal  # Total savings from promotions


# Cart operations
class AddToCartRequest(BaseModel):
    """Request to add item to cart."""
    product_id: str
    quantity: int = Field(default=1, gt=0)
    notes: Optional[str] = Field(None, max_length=500)


class UpdateCartItemRequest(BaseModel):
    """Request to update cart item."""
    quantity: int = Field(..., gt=0)
    notes: Optional[str] = Field(None, max_length=500)


class RemoveFromCartRequest(BaseModel):
    """Request to remove item from cart."""
    product_id: str


class ClearCartRequest(BaseModel):
    """Request to clear cart."""
    confirm: bool = Field(default=False, description="Confirmation to clear cart")


class MergeCartsRequest(BaseModel):
    """Request to merge carts (e.g., guest to user)."""
    source_cart_id: str
    target_cart_id: Optional[str] = None  # If None, merge to current user cart


# Saved items (wishlist) schemas
class SavedItemBase(BaseModel):
    """Base saved item schema."""
    product_id: str
    list_name: str = Field(default="Wishlist", max_length=100)
    notes: Optional[str] = Field(None, max_length=500)
    notify_on_price_drop: bool = Field(default=False)


class SavedItemCreate(SavedItemBase):
    """Schema for creating saved item."""
    pass


class SavedItemUpdate(BaseModel):
    """Schema for updating saved item."""
    list_name: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)
    notify_on_price_drop: Optional[bool] = None


class SavedItemResponse(SavedItemBase):
    """Schema for saved item response."""
    id: str
    user_id: str
    price_when_saved: Decimal
    current_price: Optional[Decimal]
    price_difference: Optional[Decimal]
    price_dropped: bool
    savings_amount: Decimal
    
    # Product info
    product_title: str
    product_image: Optional[str]
    product_brand: Optional[str]
    product_is_available: bool
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class SavedItemsList(BaseModel):
    """List of saved items grouped by list name."""
    lists: Dict[str, List[SavedItemResponse]]
    total_items: int
    price_drop_alerts: int  # Number of items with price drops


class MoveToCartRequest(BaseModel):
    """Request to move saved item to cart."""
    saved_item_id: str
    quantity: int = Field(default=1, gt=0)


# Cart validation
class CartValidationResult(BaseModel):
    """Result of cart validation."""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    unavailable_items: List[str] = []  # Product IDs
    quantity_adjustments: Dict[str, int] = {}  # Product ID -> new quantity


class CartAvailabilityCheck(BaseModel):
    """Check cart item availability."""
    product_id: str
    requested_quantity: int
    available_quantity: int
    is_available: bool
    message: Optional[str]


# Cart summary for checkout
class CartSummary(BaseModel):
    """Cart summary for checkout process."""
    cart_id: str
    total_items: int
    subtotal: Decimal
    estimated_tax: Decimal
    estimated_shipping: Decimal
    estimated_total: Decimal
    items_summary: List[Dict[str, Any]]  # Simplified item info
    requires_shipping: bool
    estimated_weight: Decimal


# Cart analytics
class CartAnalytics(BaseModel):
    """Cart analytics data."""
    active_carts: int
    abandoned_carts: int
    average_cart_value: Decimal
    average_items_per_cart: float
    conversion_rate: float
    top_cart_items: List[Dict[str, Any]]
    abandonment_rate: float


class CartAbandonmentData(BaseModel):
    """Cart abandonment tracking data."""
    cart_id: str
    user_id: Optional[str]
    session_id: Optional[str]
    cart_value: Decimal
    item_count: int
    last_activity: datetime
    abandonment_stage: str  # 'cart', 'checkout', 'payment'
    recovery_sent: bool
    recovered: bool


# Shipping estimation for cart
class ShippingEstimateRequest(BaseModel):
    """Request for shipping cost estimation."""
    cart_id: str
    shipping_address: Optional[Dict[str, str]] = None
    shipping_zone_id: Optional[str] = None


class ShippingEstimate(BaseModel):
    """Shipping cost estimate."""
    zone_name: str
    base_cost: Decimal
    weight_cost: Decimal
    total_cost: Decimal
    delivery_time: str
    is_free_shipping: bool
    free_shipping_threshold: Optional[Decimal]
    amount_for_free_shipping: Optional[Decimal]


# Promo code application
class ApplyPromoCodeRequest(BaseModel):
    """Request to apply promo code to cart."""
    cart_id: str
    promo_code: str


class PromoCodeResult(BaseModel):
    """Result of promo code application."""
    success: bool
    message: str
    discount_amount: Optional[Decimal] = None
    new_total: Optional[Decimal] = None
    promo_details: Optional[Dict[str, Any]] = None


class RemovePromoCodeRequest(BaseModel):
    """Request to remove promo code from cart."""
    cart_id: str
    promo_code: str


# Cart comparison (for A/B testing)
class CartComparison(BaseModel):
    """Compare cart configurations."""
    original_total: Decimal
    new_total: Decimal
    savings: Decimal
    changes: List[str]
    recommendations: List[str]


# Bulk cart operations
class BulkCartUpdate(BaseModel):
    """Bulk update multiple cart items."""
    updates: List[Dict[str, Any]]  # List of {product_id, quantity, notes}


class BulkRemoveFromCart(BaseModel):
    """Bulk remove items from cart."""
    product_ids: List[str] = Field(..., min_items=1)


# Cart sharing (for customer service)
class ShareCartRequest(BaseModel):
    """Request to share cart with customer service."""
    cart_id: str
    share_duration_hours: int = Field(default=24, ge=1, le=168)  # Max 1 week


class SharedCartResponse(BaseModel):
    """Response for shared cart."""
    share_token: str
    share_url: str
    expires_at: datetime


# Forward references
CartDetail.model_rebuild()
