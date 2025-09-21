"""
User models for PromoWeb Africa.
Handles user accounts, authentication, and addresses with PostGIS support.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, ForeignKey, Integer
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid

from app.core.database import Base


# User role enum
user_role_enum = ENUM(
    'customer', 'admin', 'super_admin',
    name='user_role',
    create_type=False
)


class User(Base):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile fields
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True, index=True)
    
    # Role and permissions
    role = Column(user_role_enum, default='customer', nullable=False)
    
    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    phone_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    addresses = relationship("UserAddress", back_populates="user", cascade="all, delete-orphan")
    carts = relationship("Cart", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")
    product_views = relationship("ProductView", back_populates="user")
    search_analytics = relationship("SearchAnalytic", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role in ['admin', 'super_admin']
    
    @property
    def is_super_admin(self) -> bool:
        """Check if user is super admin."""
        return self.role == 'super_admin'
    
    def get_default_address(self) -> Optional["UserAddress"]:
        """Get user's default address."""
        for address in self.addresses:
            if address.is_default:
                return address
        return self.addresses[0] if self.addresses else None


class UserAddress(Base):
    """User address model with PostGIS support for geolocation."""
    
    __tablename__ = "user_addresses"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Address fields
    name = Column(String(100), nullable=False)  # e.g., "Domicile", "Bureau"
    street_address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    region = Column(String(100), nullable=True)  # Cameroon regions
    postal_code = Column(String(10), nullable=True)
    country = Column(String(2), default='CM', nullable=False)
    
    # PostGIS geometry field for GPS coordinates
    location = Column(Geometry('POINT', srid=4326), nullable=True)
    
    # Status
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="addresses")
    shipping_orders = relationship("Order", foreign_keys="Order.shipping_address_id")
    billing_orders = relationship("Order", foreign_keys="Order.billing_address_id")
    
    def __repr__(self):
        return f"<UserAddress(id={self.id}, name='{self.name}', city='{self.city}')>"
    
    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        parts = [self.street_address, self.city]
        if self.region:
            parts.append(self.region)
        if self.postal_code:
            parts.append(self.postal_code)
        parts.append(self.country)
        return ", ".join(parts)
    
    @property
    def coordinates(self) -> Optional[tuple]:
        """Get latitude and longitude coordinates."""
        if self.location:
            return (self.location.coords[0][1], self.location.coords[0][0])  # (lat, lng)
        return None


class UserSession(Base):
    """User session model for tracking active sessions."""
    
    __tablename__ = "user_sessions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Session data
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=True, index=True)
    
    # Session metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    device_info = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at


class UserPreference(Base):
    """User preferences and settings."""
    
    __tablename__ = "user_preferences"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Preferences
    language = Column(String(10), default='fr', nullable=False)  # fr, en
    currency = Column(String(3), default='XAF', nullable=False)
    timezone = Column(String(50), default='Africa/Douala', nullable=False)
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True, nullable=False)
    sms_notifications = Column(Boolean, default=True, nullable=False)
    marketing_emails = Column(Boolean, default=False, nullable=False)
    
    # Display preferences
    items_per_page = Column(Integer, default=20, nullable=False)
    theme = Column(String(20), default='light', nullable=False)  # light, dark, auto
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id}, language='{self.language}')>"


class UserPasswordReset(Base):
    """Password reset tokens."""
    
    __tablename__ = "user_password_resets"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Token data
    token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Status
    is_used = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserPasswordReset(id={self.id}, user_id={self.user_id}, used={self.is_used})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired


class UserEmailVerification(Base):
    """Email verification tokens."""
    
    __tablename__ = "user_email_verifications"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Token data
    token = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)  # Email to verify (in case user changes it)
    
    # Status
    is_used = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserEmailVerification(id={self.id}, email='{self.email}', used={self.is_used})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired
