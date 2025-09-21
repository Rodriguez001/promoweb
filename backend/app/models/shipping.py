"""
Shipping and delivery models for PromoWeb Africa.
Handles shipping zones, carriers, tracking, and geospatial calculations.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
from decimal import Decimal
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Numeric, Text, 
    Integer, Date, Index
)
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSON
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid

from app.core.database import Base


# Shipping status enum
shipping_status_enum = ENUM(
    'pending', 'preparing', 'shipped', 'in_transit', 
    'delivered', 'failed', 'returned',
    name='shipping_status',
    create_type=False
)


class Shipping(Base):
    """Shipping information and tracking for orders."""
    
    __tablename__ = "shipping"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), unique=True, nullable=False)
    
    # Carrier information
    carrier = Column(String(100), nullable=True)
    carrier_service = Column(String(100), nullable=True)  # Standard, Express, etc.
    tracking_number = Column(String(100), nullable=True, index=True)
    tracking_url = Column(String(500), nullable=True)
    
    # Shipping details
    status = Column(shipping_status_enum, default='pending', nullable=False, index=True)
    weight_kg = Column(Numeric(8, 3), nullable=True)
    dimensions_cm = Column(String(50), nullable=True)  # "L x W x H"
    cost = Column(Numeric(10, 2), nullable=False)
    
    # Delivery information
    estimated_delivery = Column(Date, nullable=True)
    actual_delivery = Column(Date, nullable=True)
    delivery_attempts = Column(Integer, default=0, nullable=False)
    
    # Addresses (copied from order for historical record)
    pickup_address = Column(Text, nullable=True)
    delivery_address = Column(Text, nullable=False)
    delivery_location = Column(Geometry('POINT', srid=4326), nullable=True)
    
    # Delivery notes and instructions
    delivery_instructions = Column(Text, nullable=True)
    delivery_notes = Column(Text, nullable=True)  # Courier notes
    
    # Proof of delivery
    delivered_to = Column(String(200), nullable=True)  # Name of person who received
    signature_url = Column(String(500), nullable=True)  # Digital signature image
    photo_url = Column(String(500), nullable=True)     # Delivery photo
    
    # Timestamps
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="shipping")
    tracking_events = relationship("ShippingTrackingEvent", back_populates="shipping", 
                                 cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_shipping_status', 'status'),
        Index('idx_shipping_tracking', 'tracking_number'),
        Index('idx_shipping_delivery_location', 'delivery_location', postgresql_using='gist'),
    )
    
    def __repr__(self):
        return f"<Shipping(id={self.id}, order_id={self.order_id}, status='{self.status}')>"
    
    @validates('cost')
    def validate_cost(self, key, value):
        """Validate shipping cost is non-negative."""
        if value < 0:
            raise ValueError("Shipping cost cannot be negative")
        return value
    
    @property
    def is_delivered(self) -> bool:
        """Check if shipment is delivered."""
        return self.status == 'delivered'
    
    @property
    def is_in_transit(self) -> bool:
        """Check if shipment is in transit."""
        return self.status in ['shipped', 'in_transit']
    
    @property
    def delivery_status_display(self) -> str:
        """Get user-friendly delivery status."""
        status_map = {
            'pending': 'Préparation en cours',
            'preparing': 'Préparation de votre commande',
            'shipped': 'Expédié',
            'in_transit': 'En cours de livraison',
            'delivered': 'Livré',
            'failed': 'Échec de livraison',
            'returned': 'Retourné à l\'expéditeur'
        }
        return status_map.get(self.status, self.status)
    
    @property
    def estimated_delivery_days(self) -> Optional[int]:
        """Get estimated delivery time in days from now."""
        if self.estimated_delivery:
            today = date.today()
            if self.estimated_delivery > today:
                return (self.estimated_delivery - today).days
        return None
    
    @property
    def is_overdue(self) -> bool:
        """Check if delivery is overdue."""
        if self.estimated_delivery and not self.is_delivered:
            return date.today() > self.estimated_delivery
        return False
    
    def update_status(self, new_status: str, notes: str = None, location: str = None) -> None:
        """Update shipping status and create tracking event."""
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        # Set timestamps for specific statuses
        if new_status == 'shipped' and not self.shipped_at:
            self.shipped_at = datetime.utcnow()
        elif new_status == 'delivered':
            self.delivered_at = datetime.utcnow()
            self.actual_delivery = date.today()
        
        # Create tracking event
        event = ShippingTrackingEvent(
            shipping_id=self.id,
            status=new_status,
            description=notes or f"Status updated to {self.delivery_status_display}",
            location=location
        )
        self.tracking_events.append(event)
    
    def calculate_shipping_cost(self, shipping_zone: "ShippingZone") -> Decimal:
        """Calculate shipping cost based on zone and package details."""
        base_cost = shipping_zone.base_cost
        
        # Add weight-based cost
        if self.weight_kg and shipping_zone.cost_per_kg:
            weight_cost = self.weight_kg * shipping_zone.cost_per_kg
            base_cost += weight_cost
        
        return base_cost
    
    def get_latest_tracking_event(self) -> Optional["ShippingTrackingEvent"]:
        """Get the latest tracking event."""
        if self.tracking_events:
            return sorted(self.tracking_events, key=lambda x: x.created_at, reverse=True)[0]
        return None
    
    def increment_delivery_attempts(self) -> None:
        """Increment delivery attempt counter."""
        self.delivery_attempts += 1
        self.updated_at = datetime.utcnow()


class ShippingTrackingEvent(Base):
    """Individual tracking events for shipments."""
    
    __tablename__ = "shipping_tracking_events"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    shipping_id = Column(UUID(as_uuid=True), ForeignKey("shipping.id", ondelete="CASCADE"), nullable=False)
    
    # Event details
    status = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(200), nullable=True)
    
    # Additional data from carrier API
    carrier_event_id = Column(String(100), nullable=True)
    carrier_data = Column(JSON, nullable=True)
    
    # Timestamp
    event_time = Column(DateTime(timezone=True), nullable=True)  # Time from carrier
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship
    shipping = relationship("Shipping", back_populates="tracking_events")
    
    # Indexes
    __table_args__ = (
        Index('idx_tracking_event_shipping', 'shipping_id'),
        Index('idx_tracking_event_time', 'event_time'),
    )
    
    def __repr__(self):
        return f"<ShippingTrackingEvent(id={self.id}, status='{self.status}')>"


class ShippingZone(Base):
    """Geographic shipping zones with pricing rules."""
    
    __tablename__ = "shipping_zones"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Zone information
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    
    # Geographic boundaries (PostGIS)
    zone_geometry = Column(Geometry('MULTIPOLYGON', srid=4326), nullable=True)
    
    # Pricing
    base_cost = Column(Numeric(10, 2), nullable=False)
    cost_per_kg = Column(Numeric(10, 2), nullable=False)
    free_shipping_threshold = Column(Numeric(10, 2), nullable=True)
    
    # Delivery time
    min_delivery_days = Column(Integer, default=1, nullable=False)
    max_delivery_days = Column(Integer, default=3, nullable=False)
    
    # Restrictions
    max_weight_kg = Column(Numeric(8, 3), nullable=True)
    restricted_items = Column(JSON, default=list, nullable=False)  # List of restricted item types
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_shipping_zone_geometry', 'zone_geometry', postgresql_using='gist'),
        Index('idx_shipping_zone_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<ShippingZone(id={self.id}, name='{self.name}', code='{self.code}')>"
    
    @property
    def delivery_time_display(self) -> str:
        """Get delivery time range display."""
        if self.min_delivery_days == self.max_delivery_days:
            return f"{self.min_delivery_days} jour{'s' if self.min_delivery_days > 1 else ''}"
        return f"{self.min_delivery_days}-{self.max_delivery_days} jours"
    
    def calculate_cost(self, weight_kg: Decimal, order_total: Decimal = None) -> Decimal:
        """Calculate shipping cost for given weight and order total."""
        # Check for free shipping
        if (self.free_shipping_threshold and order_total and 
            order_total >= self.free_shipping_threshold):
            return Decimal('0')
        
        # Calculate cost
        cost = self.base_cost
        if weight_kg:
            cost += weight_kg * self.cost_per_kg
        
        return cost
    
    def can_ship_weight(self, weight_kg: Decimal) -> bool:
        """Check if zone can ship given weight."""
        return not self.max_weight_kg or weight_kg <= self.max_weight_kg
    
    def can_ship_items(self, item_types: List[str]) -> bool:
        """Check if zone can ship given item types."""
        return not any(item_type in self.restricted_items for item_type in item_types)


class Carrier(Base):
    """Shipping carrier information and configuration."""
    
    __tablename__ = "carriers"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Carrier information
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)
    website = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # API configuration
    api_enabled = Column(Boolean, default=False, nullable=False)
    api_endpoint = Column(String(255), nullable=True)
    api_key = Column(String(255), nullable=True)  # Encrypted
    api_config = Column(JSON, nullable=True)  # Additional API configuration
    
    # Services offered
    services = Column(JSON, default=list, nullable=False)  # List of service types
    
    # Tracking
    tracking_url_template = Column(String(500), nullable=True)  # URL with {tracking_number} placeholder
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Carrier(id={self.id}, name='{self.name}', code='{self.code}')>"
    
    def get_tracking_url(self, tracking_number: str) -> Optional[str]:
        """Get tracking URL for given tracking number."""
        if self.tracking_url_template and tracking_number:
            return self.tracking_url_template.format(tracking_number=tracking_number)
        return None
    
    def has_service(self, service_type: str) -> bool:
        """Check if carrier offers specific service type."""
        return service_type in self.services


class DeliveryAttempt(Base):
    """Record of delivery attempts."""
    
    __tablename__ = "delivery_attempts"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    shipping_id = Column(UUID(as_uuid=True), ForeignKey("shipping.id", ondelete="CASCADE"), nullable=False)
    
    # Attempt details
    attempt_number = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)  # 'delivered', 'failed', 'rescheduled'
    
    # Failure reason (if failed)
    failure_reason = Column(String(255), nullable=True)
    failure_notes = Column(Text, nullable=True)
    
    # Delivery details (if successful)
    delivered_to = Column(String(200), nullable=True)
    signature_url = Column(String(500), nullable=True)
    photo_url = Column(String(500), nullable=True)
    
    # Next attempt scheduling
    next_attempt_date = Column(Date, nullable=True)
    next_attempt_time_slot = Column(String(50), nullable=True)  # "09:00-12:00"
    
    # Timestamp
    attempted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship
    shipping = relationship("Shipping")
    
    def __repr__(self):
        return f"<DeliveryAttempt(id={self.id}, attempt={self.attempt_number}, status='{self.status}')>"
    
    @property
    def was_successful(self) -> bool:
        """Check if delivery attempt was successful."""
        return self.status == 'delivered'
    
    @property
    def can_retry(self) -> bool:
        """Check if delivery can be retried."""
        return self.status == 'failed' and self.attempt_number < 3  # Max 3 attempts


class ShippingLabel(Base):
    """Shipping labels and documentation."""
    
    __tablename__ = "shipping_labels"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    shipping_id = Column(UUID(as_uuid=True), ForeignKey("shipping.id", ondelete="CASCADE"), nullable=False)
    
    # Label information
    label_type = Column(String(50), nullable=False)  # 'shipping_label', 'return_label', 'customs'
    format = Column(String(20), default='PDF', nullable=False)  # PDF, PNG, ZPL
    
    # File storage
    file_url = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # Label data from carrier
    carrier_label_id = Column(String(100), nullable=True)
    carrier_data = Column(JSON, nullable=True)
    
    # Status
    is_valid = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship
    shipping = relationship("Shipping")
    
    def __repr__(self):
        return f"<ShippingLabel(id={self.id}, type='{self.label_type}')>"
    
    @property
    def is_expired(self) -> bool:
        """Check if label is expired."""
        return self.expires_at and datetime.utcnow() > self.expires_at
