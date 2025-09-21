"""
Shipping endpoints for PromoWeb Africa.
Handles shipping zones, carriers, and delivery tracking.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_user, get_current_admin_user, get_db_session
from app.models.shipping import Shipping, ShippingZone, Carrier, ShippingTrackingEvent
from app.models.order import Order
from app.schemas.common import BaseResponse
from app.core.database import get_db_context
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/zones", response_model=List[dict])
async def get_shipping_zones():
    """
    Get available shipping zones.
    
    Returns list of shipping zones with pricing information.
    """
    try:
        async with get_db_context() as db:
            zones = await db.execute(
                select(ShippingZone)
                .where(ShippingZone.is_active == True)
                .order_by(ShippingZone.name.asc())
            )
            
            zones_list = []
            for zone in zones.scalars().all():
                zones_list.append({
                    "id": str(zone.id),
                    "name": zone.name,
                    "code": zone.code,
                    "description": zone.description,
                    "base_cost": float(zone.base_cost),
                    "cost_per_kg": float(zone.cost_per_kg),
                    "free_shipping_threshold": float(zone.free_shipping_threshold) if zone.free_shipping_threshold else None,
                    "delivery_time": zone.delivery_time_display,
                    "min_delivery_days": zone.min_delivery_days,
                    "max_delivery_days": zone.max_delivery_days
                })
            
            return zones_list
            
    except Exception as e:
        logger.error(f"Failed to get shipping zones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve shipping zones"
        )


@router.post("/estimate", response_model=dict)
async def estimate_shipping_cost(
    shipping_zone_id: str,
    weight_kg: float = Query(..., gt=0),
    order_total: Optional[float] = Query(None, ge=0)
):
    """
    Estimate shipping cost for given parameters.
    
    - **shipping_zone_id**: Target shipping zone
    - **weight_kg**: Total package weight in kg
    - **order_total**: Order total for free shipping calculation (optional)
    """
    try:
        async with get_db_context() as db:
            zone = await db.get(ShippingZone, shipping_zone_id)
            if not zone or not zone.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Shipping zone not found"
                )
            
            # Check weight restrictions
            if zone.max_weight_kg and weight_kg > zone.max_weight_kg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Weight exceeds maximum limit: {zone.max_weight_kg} kg"
                )
            
            # Calculate shipping cost
            from decimal import Decimal
            cost = zone.calculate_cost(Decimal(str(weight_kg)), Decimal(str(order_total)) if order_total else None)
            
            # Check for free shipping
            is_free_shipping = cost == 0
            amount_for_free_shipping = None
            
            if not is_free_shipping and zone.free_shipping_threshold and order_total:
                remaining = float(zone.free_shipping_threshold) - order_total
                if remaining > 0:
                    amount_for_free_shipping = remaining
            
            return {
                "zone_name": zone.name,
                "base_cost": float(zone.base_cost),
                "weight_cost": float(zone.cost_per_kg * Decimal(str(weight_kg))),
                "total_cost": float(cost),
                "delivery_time": zone.delivery_time_display,
                "is_free_shipping": is_free_shipping,
                "free_shipping_threshold": float(zone.free_shipping_threshold) if zone.free_shipping_threshold else None,
                "amount_for_free_shipping": amount_for_free_shipping
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to estimate shipping: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to estimate shipping cost"
        )


@router.get("/track/{tracking_number}", response_model=dict)
async def track_shipment(tracking_number: str):
    """
    Track shipment by tracking number.
    
    Returns shipping status and tracking events.
    """
    try:
        async with get_db_context() as db:
            shipping = await db.execute(
                select(Shipping)
                .where(Shipping.tracking_number == tracking_number)
                .options(
                    selectinload(Shipping.tracking_events),
                    selectinload(Shipping.order)
                )
            )
            shipping = shipping.scalar_one_or_none()
            
            if not shipping:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Tracking number not found"
                )
            
            # Format tracking events
            events = []
            for event in sorted(shipping.tracking_events, key=lambda x: x.created_at, reverse=True):
                events.append({
                    "status": event.status,
                    "description": event.description,
                    "location": event.location,
                    "event_time": event.event_time or event.created_at,
                    "created_at": event.created_at
                })
            
            return {
                "tracking_number": shipping.tracking_number,
                "status": shipping.status,
                "status_display": shipping.delivery_status_display,
                "carrier": shipping.carrier,
                "estimated_delivery": shipping.estimated_delivery,
                "actual_delivery": shipping.actual_delivery,
                "delivery_attempts": shipping.delivery_attempts,
                "is_delivered": shipping.is_delivered,
                "is_overdue": shipping.is_overdue,
                "order_number": shipping.order.order_number if shipping.order else None,
                "tracking_events": events,
                "tracking_url": shipping.tracking_url
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to track shipment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track shipment"
        )


@router.get("/order/{order_id}", response_model=dict)
async def get_order_shipping(
    order_id: str,
    current_user: object = Depends(get_current_user)
):
    """Get shipping information for an order."""
    try:
        async with get_db_context() as db:
            # Verify order ownership and get shipping
            shipping = await db.execute(
                select(Shipping)
                .join(Order)
                .where(
                    Shipping.order_id == order_id,
                    Order.user_id == current_user.id
                )
                .options(selectinload(Shipping.tracking_events))
            )
            shipping = shipping.scalar_one_or_none()
            
            if not shipping:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Shipping information not found"
                )
            
            # Format tracking events
            events = []
            for event in sorted(shipping.tracking_events, key=lambda x: x.created_at, reverse=True):
                events.append({
                    "status": event.status,
                    "description": event.description,
                    "location": event.location,
                    "event_time": event.event_time or event.created_at,
                    "created_at": event.created_at
                })
            
            return {
                "id": str(shipping.id),
                "order_id": str(shipping.order_id),
                "tracking_number": shipping.tracking_number,
                "status": shipping.status,
                "status_display": shipping.delivery_status_display,
                "carrier": shipping.carrier,
                "carrier_service": shipping.carrier_service,
                "estimated_delivery": shipping.estimated_delivery,
                "actual_delivery": shipping.actual_delivery,
                "delivery_attempts": shipping.delivery_attempts,
                "is_delivered": shipping.is_delivered,
                "is_overdue": shipping.is_overdue,
                "delivery_address": shipping.delivery_address,
                "delivery_instructions": shipping.delivery_instructions,
                "tracking_events": events,
                "tracking_url": shipping.tracking_url
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get order shipping: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve shipping information"
        )


# Admin endpoints
@router.get("/admin/carriers", response_model=List[dict])
async def list_carriers(admin_user: object = Depends(get_current_admin_user)):
    """List all carriers (admin only)."""
    try:
        async with get_db_context() as db:
            carriers = await db.execute(
                select(Carrier).order_by(Carrier.name.asc())
            )
            
            carriers_list = []
            for carrier in carriers.scalars().all():
                carriers_list.append({
                    "id": str(carrier.id),
                    "name": carrier.name,
                    "code": carrier.code,
                    "website": carrier.website,
                    "phone": carrier.phone,
                    "api_enabled": carrier.api_enabled,
                    "services": carrier.services,
                    "is_active": carrier.is_active
                })
            
            return carriers_list
            
    except Exception as e:
        logger.error(f"Failed to list carriers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve carriers"
        )


@router.post("/admin/shipping/{shipping_id}/update-status", response_model=BaseResponse)
async def update_shipping_status(
    shipping_id: str,
    status: str = Query(...),
    notes: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    admin_user: object = Depends(get_current_admin_user)
):
    """Update shipping status (admin only)."""
    try:
        async with get_db_context() as db:
            shipping = await db.get(Shipping, shipping_id)
            if not shipping:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Shipping not found"
                )
            
            # Update shipping status
            shipping.update_status(status, notes, location)
            await db.commit()
            
            logger.info(f"Shipping status updated: {shipping_id} -> {status}")
            return BaseResponse(message="Shipping status updated successfully")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update shipping status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update shipping status"
        )


@router.get("/admin/zones", response_model=List[dict])
async def list_shipping_zones_admin(admin_user: object = Depends(get_current_admin_user)):
    """List all shipping zones (admin only)."""
    try:
        async with get_db_context() as db:
            zones = await db.execute(
                select(ShippingZone).order_by(ShippingZone.name.asc())
            )
            
            zones_list = []
            for zone in zones.scalars().all():
                zones_list.append({
                    "id": str(zone.id),
                    "name": zone.name,
                    "code": zone.code,
                    "description": zone.description,
                    "base_cost": float(zone.base_cost),
                    "cost_per_kg": float(zone.cost_per_kg),
                    "free_shipping_threshold": float(zone.free_shipping_threshold) if zone.free_shipping_threshold else None,
                    "min_delivery_days": zone.min_delivery_days,
                    "max_delivery_days": zone.max_delivery_days,
                    "max_weight_kg": float(zone.max_weight_kg) if zone.max_weight_kg else None,
                    "restricted_items": zone.restricted_items,
                    "is_active": zone.is_active,
                    "created_at": zone.created_at,
                    "updated_at": zone.updated_at
                })
            
            return zones_list
            
    except Exception as e:
        logger.error(f"Failed to list shipping zones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve shipping zones"
        )
