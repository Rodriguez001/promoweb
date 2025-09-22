"""
Shipping schemas for PromoWeb Africa.
Pydantic models for shipping data validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from decimal import Decimal
from enum import Enum


# Enums
class ShippingStatus(str, Enum):
    """Shipping status options."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    RETURNED = "returned"
    FAILED = "failed"


class ShippingMethod(str, Enum):
    """Shipping method options."""
    STANDARD = "standard"
    EXPRESS = "express"
    SAME_DAY = "same_day"
    PICKUP = "pickup"


class ShippingBase(BaseModel):
    """Base shipping schema."""
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    method: ShippingMethod
    status: ShippingStatus = ShippingStatus.PENDING
    estimated_delivery: Optional[datetime] = None
    shipping_cost: Decimal
    notes: Optional[str] = None


class ShippingCreate(ShippingBase):
    """Schema for creating shipping."""
    order_id: str


class ShippingUpdate(BaseModel):
    """Schema for updating shipping."""
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    method: Optional[ShippingMethod] = None
    status: Optional[ShippingStatus] = None
    estimated_delivery: Optional[datetime] = None
    shipping_cost: Optional[Decimal] = None
    notes: Optional[str] = None
    actual_delivery: Optional[datetime] = None


class ShippingResponse(ShippingBase):
    """Schema for shipping response."""
    id: str
    order_id: str
    created_at: datetime
    updated_at: datetime
    actual_delivery: Optional[datetime] = None
    
    class Config:
        from_attributes = True
