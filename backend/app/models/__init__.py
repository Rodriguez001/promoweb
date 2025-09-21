"""
Models package for PromoWeb Africa.
Imports all SQLAlchemy models for database initialization.
"""

from app.models.user import (
    User, UserAddress, UserSession, UserPreference, 
    UserPasswordReset, UserEmailVerification
)
from app.models.product import (
    Category, Product, Inventory, ProductReview
)
from app.models.cart import (
    Cart, CartItem, SavedItem
)
from app.models.order import (
    Order, OrderItem, OrderStatusHistory
)
from app.models.payment import (
    Payment, PaymentRefund, PaymentWebhook, 
    PaymentMethod, PaymentTransaction
)
from app.models.shipping import (
    Shipping, ShippingTrackingEvent, ShippingZone, 
    Carrier, DeliveryAttempt, ShippingLabel
)
from app.models.promotion import (
    Promotion, CategoryPromotion, PromotionUsage,
    FlashSale, FlashSaleItem
)
from app.models.analytics import (
    SearchAnalytic, ProductView, CartAbandonmentEvent,
    ConversionFunnel, PerformanceMetric, ABTest, ABTestParticipant
)

__all__ = [
    # User models
    "User", "UserAddress", "UserSession", "UserPreference", 
    "UserPasswordReset", "UserEmailVerification",
    
    # Product models
    "Category", "Product", "Inventory", "ProductReview",
    
    # Cart models
    "Cart", "CartItem", "SavedItem",
    
    # Order models
    "Order", "OrderItem", "OrderStatusHistory",
    
    # Payment models
    "Payment", "PaymentRefund", "PaymentWebhook", 
    "PaymentMethod", "PaymentTransaction",
    
    # Shipping models
    "Shipping", "ShippingTrackingEvent", "ShippingZone", 
    "Carrier", "DeliveryAttempt", "ShippingLabel",
    
    # Promotion models
    "Promotion", "CategoryPromotion", "PromotionUsage",
    "FlashSale", "FlashSaleItem",
    
    # Analytics models
    "SearchAnalytic", "ProductView", "CartAbandonmentEvent",
    "ConversionFunnel", "PerformanceMetric", "ABTest", "ABTestParticipant",
]
