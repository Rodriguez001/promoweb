"""
Cart and CartItem models for PromoWeb Africa.
Handles shopping cart functionality with user sessions and guest support.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Integer, 
    Numeric, Text, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Cart(Base):
    """Shopping cart model supporting both authenticated users and guest sessions."""
    
    __tablename__ = "carts"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User or session identification
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    session_id = Column(String(255), nullable=True, index=True)  # For anonymous users
    
    # Cart totals (cached for performance)
    total_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    total_items = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # For guest carts
    
    # Relationships
    user = relationship("User", back_populates="carts")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_cart_user_session', 'user_id', 'session_id'),
        Index('idx_cart_expires', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<Cart(id={self.id}, user_id={self.user_id}, items={self.total_items})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if cart is expired (for guest carts)."""
        return self.expires_at and datetime.utcnow() > self.expires_at
    
    @property
    def is_empty(self) -> bool:
        """Check if cart is empty."""
        return self.total_items == 0
    
    def calculate_totals(self) -> Dict[str, Any]:
        """Calculate cart totals including taxes and shipping estimates."""
        subtotal = Decimal('0')
        total_weight = Decimal('0')
        item_count = 0
        
        for item in self.items:
            if item.product and item.product.is_active:
                item_total = item.get_total_price()
                subtotal += item_total
                item_count += item.quantity
                
                # Add weight for shipping calculation
                if item.product.weight_kg:
                    total_weight += item.product.weight_kg * item.quantity
        
        # Apply promotions/discounts
        discount_amount = self._calculate_discounts(subtotal)
        
        # Calculate shipping estimate
        shipping_estimate = self._estimate_shipping(total_weight)
        
        # Calculate taxes (if applicable)
        tax_amount = self._calculate_taxes(subtotal - discount_amount)
        
        final_total = subtotal - discount_amount + shipping_estimate + tax_amount
        
        return {
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'tax_amount': tax_amount,
            'shipping_estimate': shipping_estimate,
            'total': final_total,
            'item_count': item_count,
            'total_weight': total_weight,
        }
    
    def _calculate_discounts(self, subtotal: Decimal) -> Decimal:
        """Calculate applicable discounts."""
        # This would check for cart-level promotions
        # For now, return 0 as product-level promotions are handled elsewhere
        return Decimal('0')
    
    def _estimate_shipping(self, total_weight: Decimal) -> Decimal:
        """Estimate shipping cost based on weight."""
        from app.core.config import get_settings
        settings = get_settings()
        
        base_cost = Decimal(str(settings.DEFAULT_SHIPPING_COST))
        weight_cost = total_weight * Decimal(str(settings.WEIGHT_RATE_PER_KG))
        
        return base_cost + weight_cost
    
    def _calculate_taxes(self, taxable_amount: Decimal) -> Decimal:
        """Calculate taxes on taxable amount."""
        # For Cameroon, VAT is typically 19.25%
        # This could be configurable or based on product categories
        tax_rate = Decimal('0.1925')  # 19.25%
        return taxable_amount * tax_rate
    
    def update_totals(self) -> None:
        """Update cached totals."""
        totals = self.calculate_totals()
        self.total_amount = totals['total']
        self.total_items = totals['item_count']
        self.updated_at = datetime.utcnow()
    
    def add_item(self, product_id: str, quantity: int = 1) -> "CartItem":
        """Add item to cart or update quantity if exists."""
        existing_item = self.get_item(product_id)
        
        if existing_item:
            existing_item.quantity += quantity
            existing_item.updated_at = datetime.utcnow()
            return existing_item
        else:
            new_item = CartItem(
                cart_id=self.id,
                product_id=product_id,
                quantity=quantity
            )
            self.items.append(new_item)
            return new_item
    
    def remove_item(self, product_id: str) -> bool:
        """Remove item from cart."""
        item = self.get_item(product_id)
        if item:
            self.items.remove(item)
            return True
        return False
    
    def update_item_quantity(self, product_id: str, quantity: int) -> bool:
        """Update item quantity."""
        if quantity <= 0:
            return self.remove_item(product_id)
        
        item = self.get_item(product_id)
        if item:
            item.quantity = quantity
            item.updated_at = datetime.utcnow()
            return True
        return False
    
    def get_item(self, product_id: str) -> Optional["CartItem"]:
        """Get cart item by product ID."""
        for item in self.items:
            if str(item.product_id) == str(product_id):
                return item
        return None
    
    def clear(self) -> None:
        """Clear all items from cart."""
        self.items.clear()
        self.update_totals()
    
    def merge_with(self, other_cart: "Cart") -> None:
        """Merge another cart into this one."""
        for item in other_cart.items:
            self.add_item(item.product_id, item.quantity)
        
        self.update_totals()
    
    def set_expiration(self, hours: int = 24) -> None:
        """Set cart expiration time."""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
    
    def extend_expiration(self, hours: int = 24) -> None:
        """Extend cart expiration time."""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)


class CartItem(Base):
    """Individual items in a shopping cart."""
    
    __tablename__ = "cart_items"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    # Item details
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)  # Price at time of adding to cart
    total_price = Column(Numeric(10, 2), nullable=False)  # Cached total for this item
    
    # Optional customization
    notes = Column(Text, nullable=True)  # Special requests or notes
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items")
    
    # Indexes
    __table_args__ = (
        Index('idx_cart_items_cart_product', 'cart_id', 'product_id', unique=True),
    )
    
    def __repr__(self):
        return f"<CartItem(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"
    
    @validates('quantity')
    def validate_quantity(self, key, value):
        """Validate quantity is positive."""
        if value <= 0:
            raise ValueError("Quantity must be positive")
        return value
    
    def update_price(self) -> None:
        """Update unit price from current product price."""
        if self.product:
            self.unit_price = self.product.get_current_price()
            self.total_price = self.unit_price * self.quantity
    
    def get_total_price(self) -> Decimal:
        """Get total price for this item."""
        if self.product:
            current_price = self.product.get_current_price()
            return current_price * self.quantity
        return self.total_price
    
    def get_savings(self) -> Decimal:
        """Get savings from promotions."""
        if self.product:
            original_total = self.product.price_xaf * self.quantity
            current_total = self.get_total_price()
            return max(Decimal('0'), original_total - current_total)
        return Decimal('0')
    
    @property
    def is_available(self) -> bool:
        """Check if product is still available."""
        return (
            self.product and 
            self.product.is_active and 
            self.product.is_in_stock and
            self.product.stock_quantity >= self.quantity
        )
    
    @property
    def availability_message(self) -> Optional[str]:
        """Get availability message if item is not available."""
        if not self.product:
            return "Product no longer exists"
        
        if not self.product.is_active:
            return "Product is no longer available"
        
        if not self.product.is_in_stock:
            return "Product is out of stock"
        
        if self.product.stock_quantity < self.quantity:
            return f"Only {self.product.stock_quantity} items available"
        
        return None
    
    def check_availability(self) -> bool:
        """Check if item can be purchased in requested quantity."""
        return self.is_available
    
    def adjust_quantity_to_available(self) -> int:
        """Adjust quantity to available stock and return new quantity."""
        if not self.product or not self.product.is_active:
            self.quantity = 0
            return 0
        
        available = self.product.stock_quantity
        if self.quantity > available:
            self.quantity = available
        
        return self.quantity


class SavedItem(Base):
    """Items saved for later (wishlist/favorites)."""
    
    __tablename__ = "saved_items"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    
    # Optional organization
    list_name = Column(String(100), default="Wishlist", nullable=False)
    notes = Column(Text, nullable=True)
    
    # Price tracking
    price_when_saved = Column(Numeric(10, 2), nullable=False)
    notify_on_price_drop = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    product = relationship("Product")
    
    # Indexes
    __table_args__ = (
        Index('idx_saved_items_user_product', 'user_id', 'product_id', unique=True),
        Index('idx_saved_items_user_list', 'user_id', 'list_name'),
    )
    
    def __repr__(self):
        return f"<SavedItem(id={self.id}, user_id={self.user_id}, product_id={self.product_id})>"
    
    @property
    def current_price(self) -> Optional[Decimal]:
        """Get current product price."""
        return self.product.get_current_price() if self.product else None
    
    @property
    def price_difference(self) -> Optional[Decimal]:
        """Get price difference since saved."""
        current = self.current_price
        if current:
            return current - self.price_when_saved
        return None
    
    @property
    def price_dropped(self) -> bool:
        """Check if price has dropped since saved."""
        diff = self.price_difference
        return diff is not None and diff < 0
    
    @property
    def savings_amount(self) -> Decimal:
        """Get savings amount if price dropped."""
        diff = self.price_difference
        return abs(diff) if diff and diff < 0 else Decimal('0')
    
    def move_to_cart(self, cart: Cart, quantity: int = 1) -> CartItem:
        """Move saved item to cart."""
        return cart.add_item(self.product_id, quantity)
