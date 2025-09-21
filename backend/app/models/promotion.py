"""
Promotion and discount models for PromoWeb Africa.
Handles coupon codes, product promotions, and discount calculations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Numeric, Text, 
    Integer, Table, Index
)
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSON
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


# Promotion type enum
promotion_type_enum = ENUM(
    'percentage', 'fixed_amount', 'free_shipping', 'buy_one_get_one',
    name='promotion_type',
    create_type=False
)

# Association table for many-to-many relationship between products and promotions
product_promotions = Table(
    'product_promotions',
    Base.metadata,
    Column('product_id', UUID(as_uuid=True), ForeignKey('products.id', ondelete='CASCADE'), primary_key=True),
    Column('promotion_id', UUID(as_uuid=True), ForeignKey('promotions.id', ondelete='CASCADE'), primary_key=True)
)


class Promotion(Base):
    """Promotion model for discounts and special offers."""
    
    __tablename__ = "promotions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    code = Column(String(50), unique=True, nullable=True, index=True)  # Coupon code
    
    # Promotion type and value
    type = Column(promotion_type_enum, nullable=False)
    discount_value = Column(Numeric(10, 2), nullable=False)  # Percentage or fixed amount
    
    # Conditions
    min_order_amount = Column(Numeric(10, 2), nullable=True)  # Minimum order value
    max_discount_amount = Column(Numeric(10, 2), nullable=True)  # Maximum discount cap
    min_quantity = Column(Integer, nullable=True)  # Minimum quantity required
    
    # Usage limits
    usage_limit = Column(Integer, nullable=True)  # Total usage limit
    usage_limit_per_user = Column(Integer, nullable=True)  # Per user limit
    used_count = Column(Integer, default=0, nullable=False)
    
    # Target audience
    first_time_customers_only = Column(Boolean, default=False, nullable=False)
    user_group_ids = Column(JSON, default=list, nullable=False)  # Specific user groups
    
    # Geographic restrictions
    allowed_regions = Column(JSON, default=list, nullable=False)  # List of allowed regions
    excluded_regions = Column(JSON, default=list, nullable=False)  # List of excluded regions
    
    # Time validity
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_stackable = Column(Boolean, default=False, nullable=False)  # Can be combined with other promotions
    
    # Priority (higher number = higher priority)
    priority = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    products = relationship("Product", secondary=product_promotions, back_populates="promotions")
    category_promotions = relationship("CategoryPromotion", back_populates="promotion", cascade="all, delete-orphan")
    usages = relationship("PromotionUsage", back_populates="promotion", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_promotion_active_dates', 'is_active', 'start_date', 'end_date'),
        Index('idx_promotion_code', 'code'),
        Index('idx_promotion_type', 'type'),
    )
    
    def __repr__(self):
        return f"<Promotion(id={self.id}, name='{self.name}', code='{self.code}')>"
    
    @validates('discount_value')
    def validate_discount_value(self, key, value):
        """Validate discount value based on promotion type."""
        if value < 0:
            raise ValueError("Discount value cannot be negative")
        
        if hasattr(self, 'type') and self.type == 'percentage' and value > 100:
            raise ValueError("Percentage discount cannot exceed 100%")
        
        return value
    
    @property
    def is_valid_now(self) -> bool:
        """Check if promotion is currently valid."""
        now = datetime.utcnow()
        return (
            self.is_active and
            self.start_date <= now <= self.end_date and
            (self.usage_limit is None or self.used_count < self.usage_limit)
        )
    
    @property
    def is_code_based(self) -> bool:
        """Check if promotion requires a code."""
        return self.code is not None
    
    @property
    def usage_percentage(self) -> float:
        """Get usage percentage."""
        if self.usage_limit:
            return (self.used_count / self.usage_limit) * 100
        return 0.0
    
    @property
    def discount_display(self) -> str:
        """Get user-friendly discount display."""
        if self.type == 'percentage':
            return f"{self.discount_value}% de réduction"
        elif self.type == 'fixed_amount':
            return f"{self.discount_value} XAF de réduction"
        elif self.type == 'free_shipping':
            return "Livraison gratuite"
        elif self.type == 'buy_one_get_one':
            return "Achetez 1, obtenez 1 gratuit"
        return f"{self.discount_value} de réduction"
    
    def can_be_used_by_user(self, user_id: str, user_order_count: int = 0, 
                           user_region: str = None) -> tuple[bool, Optional[str]]:
        """
        Check if promotion can be used by a specific user.
        
        Returns:
            tuple: (can_use: bool, reason: Optional[str])
        """
        # Check if promotion is valid
        if not self.is_valid_now:
            return False, "Promotion expirée ou inactive"
        
        # Check first-time customer restriction
        if self.first_time_customers_only and user_order_count > 0:
            return False, "Réservé aux nouveaux clients"
        
        # Check user group restrictions
        if self.user_group_ids and user_id not in self.user_group_ids:
            return False, "Promotion non disponible pour votre profil"
        
        # Check regional restrictions
        if user_region:
            if self.excluded_regions and user_region in self.excluded_regions:
                return False, f"Promotion non disponible dans la région {user_region}"
            
            if self.allowed_regions and user_region not in self.allowed_regions:
                return False, f"Promotion non disponible dans la région {user_region}"
        
        # Check per-user usage limit
        if self.usage_limit_per_user:
            user_usage_count = len([u for u in self.usages if u.user_id == user_id])
            if user_usage_count >= self.usage_limit_per_user:
                return False, "Limite d'utilisation atteinte pour cet utilisateur"
        
        return True, None
    
    def calculate_discount(self, order_amount: Decimal, quantity: int = 1) -> Decimal:
        """Calculate discount amount for given order."""
        if not self.is_valid_now:
            return Decimal('0')
        
        # Check minimum order amount
        if self.min_order_amount and order_amount < self.min_order_amount:
            return Decimal('0')
        
        # Check minimum quantity
        if self.min_quantity and quantity < self.min_quantity:
            return Decimal('0')
        
        discount = Decimal('0')
        
        if self.type == 'percentage':
            discount = order_amount * (self.discount_value / 100)
        elif self.type == 'fixed_amount':
            discount = self.discount_value
        elif self.type == 'free_shipping':
            # This would be handled at the shipping calculation level
            discount = Decimal('0')
        elif self.type == 'buy_one_get_one':
            # Calculate BOGO discount (assuming cheapest item free)
            if quantity >= 2:
                # This is simplified - in reality, you'd need product prices
                discount = order_amount / quantity  # Price of one item
        
        # Apply maximum discount cap
        if self.max_discount_amount:
            discount = min(discount, self.max_discount_amount)
        
        # Ensure discount doesn't exceed order amount
        discount = min(discount, order_amount)
        
        return discount
    
    def increment_usage(self, user_id: str = None, order_id: str = None) -> "PromotionUsage":
        """Record promotion usage."""
        self.used_count += 1
        self.updated_at = datetime.utcnow()
        
        usage = PromotionUsage(
            promotion_id=self.id,
            user_id=user_id,
            order_id=order_id
        )
        self.usages.append(usage)
        
        return usage
    
    def get_applicable_products(self) -> List["Product"]:
        """Get all products this promotion applies to."""
        applicable_products = list(self.products)
        
        # Add products from category promotions
        for cat_promo in self.category_promotions:
            applicable_products.extend(cat_promo.category.products)
        
        return list(set(applicable_products))  # Remove duplicates


class CategoryPromotion(Base):
    """Link promotions to product categories."""
    
    __tablename__ = "category_promotions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    promotion_id = Column(UUID(as_uuid=True), ForeignKey("promotions.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    
    # Settings
    include_subcategories = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    promotion = relationship("Promotion", back_populates="category_promotions")
    category = relationship("Category")
    
    # Indexes
    __table_args__ = (
        Index('idx_category_promotion_unique', 'promotion_id', 'category_id', unique=True),
    )
    
    def __repr__(self):
        return f"<CategoryPromotion(promotion_id={self.promotion_id}, category_id={self.category_id})>"


class PromotionUsage(Base):
    """Track promotion usage by users and orders."""
    
    __tablename__ = "promotion_usages"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    promotion_id = Column(UUID(as_uuid=True), ForeignKey("promotions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    
    # Usage details
    discount_amount = Column(Numeric(10, 2), nullable=True)
    original_amount = Column(Numeric(10, 2), nullable=True)
    
    # Metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Timestamp
    used_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    promotion = relationship("Promotion", back_populates="usages")
    user = relationship("User")
    order = relationship("Order")
    
    # Indexes
    __table_args__ = (
        Index('idx_promotion_usage_promotion', 'promotion_id'),
        Index('idx_promotion_usage_user', 'user_id'),
        Index('idx_promotion_usage_used_at', 'used_at'),
    )
    
    def __repr__(self):
        return f"<PromotionUsage(id={self.id}, promotion_id={self.promotion_id}, user_id={self.user_id})>"


class FlashSale(Base):
    """Flash sales with time-limited offers."""
    
    __tablename__ = "flash_sales"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Flash sale timing
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    
    # Display settings
    banner_image_url = Column(String(500), nullable=True)
    countdown_text = Column(String(100), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    items = relationship("FlashSaleItem", back_populates="flash_sale", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FlashSale(id={self.id}, name='{self.name}')>"
    
    @property
    def is_active_now(self) -> bool:
        """Check if flash sale is currently active."""
        now = datetime.utcnow()
        return self.is_active and self.start_time <= now <= self.end_time
    
    @property
    def time_remaining(self) -> Optional[int]:
        """Get remaining time in seconds."""
        if self.is_active_now:
            return int((self.end_time - datetime.utcnow()).total_seconds())
        return None
    
    @property
    def has_started(self) -> bool:
        """Check if flash sale has started."""
        return datetime.utcnow() >= self.start_time
    
    @property
    def has_ended(self) -> bool:
        """Check if flash sale has ended."""
        return datetime.utcnow() > self.end_time


class FlashSaleItem(Base):
    """Individual products in a flash sale."""
    
    __tablename__ = "flash_sale_items"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    flash_sale_id = Column(UUID(as_uuid=True), ForeignKey("flash_sales.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    
    # Flash sale pricing
    original_price = Column(Numeric(10, 2), nullable=False)
    sale_price = Column(Numeric(10, 2), nullable=False)
    discount_percentage = Column(Numeric(5, 2), nullable=False)
    
    # Inventory limits
    available_quantity = Column(Integer, nullable=True)  # Limited quantity
    sold_quantity = Column(Integer, default=0, nullable=False)
    
    # Display settings
    sort_order = Column(Integer, default=0, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    flash_sale = relationship("FlashSale", back_populates="items")
    product = relationship("Product")
    
    # Indexes
    __table_args__ = (
        Index('idx_flash_sale_item_unique', 'flash_sale_id', 'product_id', unique=True),
        Index('idx_flash_sale_item_sort', 'flash_sale_id', 'sort_order'),
    )
    
    def __repr__(self):
        return f"<FlashSaleItem(id={self.id}, product_id={self.product_id}, sale_price={self.sale_price})>"
    
    @property
    def savings_amount(self) -> Decimal:
        """Get savings amount."""
        return self.original_price - self.sale_price
    
    @property
    def is_available(self) -> bool:
        """Check if item is still available."""
        if self.available_quantity is None:
            return True
        return self.sold_quantity < self.available_quantity
    
    @property
    def remaining_quantity(self) -> Optional[int]:
        """Get remaining quantity."""
        if self.available_quantity is None:
            return None
        return max(0, self.available_quantity - self.sold_quantity)
    
    @property
    def sold_percentage(self) -> float:
        """Get sold percentage."""
        if self.available_quantity:
            return (self.sold_quantity / self.available_quantity) * 100
        return 0.0
    
    def record_sale(self, quantity: int = 1) -> None:
        """Record sale of this flash sale item."""
        self.sold_quantity += quantity
