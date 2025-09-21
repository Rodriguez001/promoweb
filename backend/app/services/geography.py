"""
Geography and delivery zone service for PromoWeb Africa.
Handles delivery zones, shipping calculations, and geographic features using PostGIS.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_DWithin, ST_Contains, ST_Distance
from shapely.geometry import Point, Polygon
from shapely.wkt import loads as wkt_loads

from app.core.config import get_settings
from app.core.database import get_db_context
from app.models.shipping import ShippingZone, Carrier, DeliveryAttempt
from app.models.user import UserAddress

logger = logging.getLogger(__name__)
settings = get_settings()


class DeliveryZoneType(str, Enum):
    """Delivery zone types for Cameroon."""
    DOUALA_CENTER = "douala_center"
    DOUALA_SUBURBS = "douala_suburbs"
    YAOUNDE_CENTER = "yaounde_center"
    YAOUNDE_SUBURBS = "yaounde_suburbs"
    REGIONAL_CAPITAL = "regional_capital"
    URBAN_AREA = "urban_area"
    RURAL_AREA = "rural_area"
    REMOTE_AREA = "remote_area"


@dataclass
class DeliveryZone:
    """Delivery zone information."""
    id: str
    name: str
    zone_type: DeliveryZoneType
    base_cost: Decimal
    per_kg_cost: Decimal
    max_weight_kg: Optional[float]
    estimated_days: int
    is_active: bool
    geometry: Optional[str]  # WKT format


@dataclass
class ShippingCalculation:
    """Shipping cost calculation result."""
    zone: DeliveryZone
    base_cost: Decimal
    weight_cost: Decimal
    total_cost: Decimal
    estimated_delivery_days: int
    carrier_options: List[Dict[str, Any]]
    is_available: bool
    restrictions: List[str]


class GeographyService:
    """Service for handling geographic operations and delivery zones."""
    
    def __init__(self):
        # Cameroon major cities coordinates
        self.major_cities = {
            "douala": {"lat": 4.0483, "lng": 9.7043},
            "yaounde": {"lat": 3.8480, "lng": 11.5021},
            "bamenda": {"lat": 5.9597, "lng": 10.1489},
            "bafoussam": {"lat": 5.4737, "lng": 10.4158},
            "garoua": {"lat": 9.3265, "lng": 13.3958},
            "maroua": {"lat": 10.5906, "lng": 14.3197},
            "ngaoundere": {"lat": 7.3167, "lng": 13.5833},
            "bertoua": {"lat": 4.5774, "lng": 13.6846},
            "ebolowa": {"lat": 2.9154, "lng": 11.1543},
            "kumba": {"lat": 4.6364, "lng": 9.4469}
        }
        
        # Default delivery zones configuration
        self.default_zones = [
            {
                "name": "Douala Centre",
                "zone_type": DeliveryZoneType.DOUALA_CENTER,
                "base_cost": Decimal("1500"),
                "per_kg_cost": Decimal("500"),
                "max_weight_kg": 50.0,
                "estimated_days": 1,
                "radius_km": 10
            },
            {
                "name": "Douala Banlieue",
                "zone_type": DeliveryZoneType.DOUALA_SUBURBS,
                "base_cost": Decimal("2500"),
                "per_kg_cost": Decimal("750"),
                "max_weight_kg": 30.0,
                "estimated_days": 2,
                "radius_km": 25
            },
            {
                "name": "Yaoundé Centre",
                "zone_type": DeliveryZoneType.YAOUNDE_CENTER,
                "base_cost": Decimal("1500"),
                "per_kg_cost": Decimal("500"),
                "max_weight_kg": 50.0,
                "estimated_days": 2,
                "radius_km": 10
            },
            {
                "name": "Yaoundé Banlieue",
                "zone_type": DeliveryZoneType.YAOUNDE_SUBURBS,
                "base_cost": Decimal("2500"),
                "per_kg_cost": Decimal("750"),
                "max_weight_kg": 30.0,
                "estimated_days": 3,
                "radius_km": 25
            },
            {
                "name": "Chefs-lieux de Région",
                "zone_type": DeliveryZoneType.REGIONAL_CAPITAL,
                "base_cost": Decimal("4000"),
                "per_kg_cost": Decimal("1000"),
                "max_weight_kg": 25.0,
                "estimated_days": 5,
                "radius_km": 15
            },
            {
                "name": "Zones Urbaines",
                "zone_type": DeliveryZoneType.URBAN_AREA,
                "base_cost": Decimal("6000"),
                "per_kg_cost": Decimal("1500"),
                "max_weight_kg": 20.0,
                "estimated_days": 7,
                "radius_km": None
            },
            {
                "name": "Zones Rurales",
                "zone_type": DeliveryZoneType.RURAL_AREA,
                "base_cost": Decimal("8000"),
                "per_kg_cost": Decimal("2000"),
                "max_weight_kg": 15.0,
                "estimated_days": 10,
                "radius_km": None
            }
        ]
    
    async def calculate_shipping_cost(
        self, 
        destination: UserAddress, 
        total_weight_kg: float,
        total_value: Decimal
    ) -> ShippingCalculation:
        """Calculate shipping cost for a destination."""
        try:
            # Get delivery zone for destination
            zone = await self.get_delivery_zone(destination)
            
            # Calculate costs
            base_cost = zone.base_cost
            
            # Weight-based cost calculation
            if total_weight_kg > 0:
                weight_cost = zone.per_kg_cost * Decimal(str(total_weight_kg))
            else:
                weight_cost = Decimal("0")
            
            # Check weight restrictions
            restrictions = []
            is_available = True
            
            if zone.max_weight_kg and total_weight_kg > zone.max_weight_kg:
                restrictions.append(f"Poids maximum autorisé: {zone.max_weight_kg}kg")
                is_available = False
            
            # Free shipping threshold
            free_shipping_threshold = Decimal("50000")  # 50,000 XAF
            if total_value >= free_shipping_threshold:
                base_cost = Decimal("0")
                weight_cost = weight_cost * Decimal("0.5")  # 50% discount on weight
            
            total_cost = base_cost + weight_cost
            
            # Get carrier options
            carrier_options = await self.get_carrier_options(zone, total_weight_kg)
            
            return ShippingCalculation(
                zone=zone,
                base_cost=base_cost,
                weight_cost=weight_cost,
                total_cost=total_cost,
                estimated_delivery_days=zone.estimated_days,
                carrier_options=carrier_options,
                is_available=is_available,
                restrictions=restrictions
            )
            
        except Exception as e:
            logger.error(f"Shipping calculation failed: {e}")
            # Return default zone calculation
            return await self._get_default_shipping_calculation(total_weight_kg)
    
    async def get_delivery_zone(self, address: UserAddress) -> DeliveryZone:
        """Determine delivery zone for an address."""
        try:
            async with get_db_context() as db:
                # First try to find exact zone match using PostGIS
                if address.latitude and address.longitude:
                    point = Point(address.longitude, address.latitude)
                    zone = await self._find_zone_by_geometry(db, point)
                    if zone:
                        return zone
                
                # Fallback to city-based matching
                city = address.city.lower() if address.city else ""
                
                # Check for major cities
                if "douala" in city:
                    if any(suburb in city for suburb in ["akwa", "bonanjo", "bonapriso", "centre"]):
                        return self._create_zone_from_config(self.default_zones[0])  # Douala Center
                    else:
                        return self._create_zone_from_config(self.default_zones[1])  # Douala Suburbs
                
                elif "yaoundé" in city or "yaounde" in city:
                    if any(center in city for center in ["centre", "mfoundi", "centre-ville"]):
                        return self._create_zone_from_config(self.default_zones[2])  # Yaoundé Center
                    else:
                        return self._create_zone_from_config(self.default_zones[3])  # Yaoundé Suburbs
                
                # Check for regional capitals
                regional_capitals = ["bamenda", "bafoussam", "garoua", "maroua", "ngaoundere", "bertoua", "ebolowa"]
                if any(capital in city for capital in regional_capitals):
                    return self._create_zone_from_config(self.default_zones[4])  # Regional Capital
                
                # Default to rural zone
                return self._create_zone_from_config(self.default_zones[6])  # Rural Area
                
        except Exception as e:
            logger.error(f"Failed to determine delivery zone: {e}")
            return self._create_zone_from_config(self.default_zones[6])  # Default to rural
    
    async def get_delivery_options(self, destination: UserAddress) -> List[Dict[str, Any]]:
        """Get available delivery options for a destination."""
        try:
            zone = await self.get_delivery_zone(destination)
            
            options = []
            
            # Standard delivery
            options.append({
                "id": "standard",
                "name": "Livraison Standard",
                "description": f"Livraison en {zone.estimated_days} jours ouvrables",
                "cost": zone.base_cost,
                "estimated_days": zone.estimated_days,
                "is_recommended": True
            })
            
            # Express delivery (only for major cities)
            if zone.zone_type in [DeliveryZoneType.DOUALA_CENTER, DeliveryZoneType.YAOUNDE_CENTER]:
                options.append({
                    "id": "express",
                    "name": "Livraison Express",
                    "description": "Livraison le jour même (commande avant 14h)",
                    "cost": zone.base_cost * Decimal("2"),
                    "estimated_days": 0,
                    "is_recommended": False
                })
            
            # Pickup points (for urban areas)
            if zone.zone_type in [
                DeliveryZoneType.DOUALA_CENTER,
                DeliveryZoneType.DOUALA_SUBURBS,
                DeliveryZoneType.YAOUNDE_CENTER,
                DeliveryZoneType.YAOUNDE_SUBURBS,
                DeliveryZoneType.REGIONAL_CAPITAL
            ]:
                options.append({
                    "id": "pickup",
                    "name": "Point de Retrait",
                    "description": "Retrait en point relais",
                    "cost": zone.base_cost * Decimal("0.7"),  # 30% discount
                    "estimated_days": zone.estimated_days,
                    "is_recommended": False
                })
            
            return options
            
        except Exception as e:
            logger.error(f"Failed to get delivery options: {e}")
            return []
    
    async def validate_delivery_address(self, address: UserAddress) -> Dict[str, Any]:
        """Validate and geocode a delivery address."""
        try:
            validation_result = {
                "is_valid": True,
                "suggestions": [],
                "warnings": [],
                "coordinates": None
            }
            
            # Basic validation
            if not address.city:
                validation_result["is_valid"] = False
                validation_result["warnings"].append("Ville requise")
            
            if not address.address_line_1:
                validation_result["is_valid"] = False
                validation_result["warnings"].append("Adresse requise")
            
            # Try to geocode if we don't have coordinates
            if not address.latitude or not address.longitude:
                coordinates = await self._geocode_address(address)
                if coordinates:
                    validation_result["coordinates"] = coordinates
                    validation_result["suggestions"].append("Coordonnées géographiques ajoutées")
            
            # Check if address is in serviceable area
            zone = await self.get_delivery_zone(address)
            if zone.zone_type == DeliveryZoneType.REMOTE_AREA:
                validation_result["warnings"].append("Zone de livraison éloignée - délais prolongés")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Address validation failed: {e}")
            return {"is_valid": False, "warnings": ["Erreur de validation"]}
    
    async def get_nearby_pickup_points(self, address: UserAddress, radius_km: float = 5) -> List[Dict[str, Any]]:
        """Get nearby pickup points for an address."""
        try:
            # For now, return static pickup points for major cities
            city = address.city.lower() if address.city else ""
            
            pickup_points = []
            
            if "douala" in city:
                pickup_points = [
                    {
                        "id": "douala_akwa",
                        "name": "Point Relais Akwa",
                        "address": "Boulevard de la Liberté, Akwa, Douala",
                        "phone": "+237 233 42 12 34",
                        "hours": "Lun-Sam: 8h-18h",
                        "coordinates": {"lat": 4.0501, "lng": 9.6969}
                    },
                    {
                        "id": "douala_bonanjo",
                        "name": "Centre Commercial Bonanjo",
                        "address": "Rue Joss, Bonanjo, Douala",
                        "phone": "+237 233 42 56 78",
                        "hours": "Lun-Dim: 9h-20h",
                        "coordinates": {"lat": 4.0522, "lng": 9.7021}
                    }
                ]
            
            elif "yaoundé" in city or "yaounde" in city:
                pickup_points = [
                    {
                        "id": "yaounde_centre",
                        "name": "Point Relais Centre-Ville",
                        "address": "Avenue Kennedy, Centre-Ville, Yaoundé",
                        "phone": "+237 222 23 45 67",
                        "hours": "Lun-Sam: 8h-18h",
                        "coordinates": {"lat": 3.8667, "lng": 11.5167}
                    },
                    {
                        "id": "yaounde_nlongkak",
                        "name": "Centre Nlongkak",
                        "address": "Carrefour Nlongkak, Yaoundé",
                        "phone": "+237 222 23 89 01",
                        "hours": "Lun-Sam: 9h-19h",
                        "coordinates": {"lat": 3.8886, "lng": 11.5021}
                    }
                ]
            
            return pickup_points
            
        except Exception as e:
            logger.error(f"Failed to get pickup points: {e}")
            return []
    
    async def _find_zone_by_geometry(self, db: AsyncSession, point: Point) -> Optional[DeliveryZone]:
        """Find delivery zone using PostGIS geometry operations."""
        try:
            # Query shipping zones using PostGIS
            result = await db.execute(
                select(ShippingZone)
                .where(ST_Contains(ShippingZone.geometry, f"POINT({point.x} {point.y})"))
                .limit(1)
            )
            
            zone_record = result.scalar_one_or_none()
            if zone_record:
                return DeliveryZone(
                    id=str(zone_record.id),
                    name=zone_record.name,
                    zone_type=DeliveryZoneType(zone_record.zone_type),
                    base_cost=zone_record.base_cost,
                    per_kg_cost=zone_record.per_kg_cost,
                    max_weight_kg=zone_record.max_weight_kg,
                    estimated_days=zone_record.estimated_delivery_days,
                    is_active=zone_record.is_active,
                    geometry=str(zone_record.geometry) if zone_record.geometry else None
                )
            
            return None
            
        except Exception as e:
            logger.error(f"PostGIS zone lookup failed: {e}")
            return None
    
    def _create_zone_from_config(self, config: Dict[str, Any]) -> DeliveryZone:
        """Create delivery zone from configuration."""
        return DeliveryZone(
            id=config["zone_type"],
            name=config["name"],
            zone_type=config["zone_type"],
            base_cost=config["base_cost"],
            per_kg_cost=config["per_kg_cost"],
            max_weight_kg=config["max_weight_kg"],
            estimated_days=config["estimated_days"],
            is_active=True,
            geometry=None
        )
    
    async def get_carrier_options(self, zone: DeliveryZone, weight_kg: float) -> List[Dict[str, Any]]:
        """Get available carriers for a zone."""
        carriers = []
        
        # DHL (for major cities and light packages)
        if zone.zone_type in [DeliveryZoneType.DOUALA_CENTER, DeliveryZoneType.YAOUNDE_CENTER] and weight_kg <= 10:
            carriers.append({
                "id": "dhl",
                "name": "DHL Express",
                "description": "Livraison rapide et sécurisée",
                "cost_multiplier": 2.5,
                "estimated_days": max(1, zone.estimated_days - 1)
            })
        
        # UPS (for business addresses)
        if zone.zone_type in [DeliveryZoneType.DOUALA_CENTER, DeliveryZoneType.YAOUNDE_CENTER]:
            carriers.append({
                "id": "ups",
                "name": "UPS",
                "description": "Service professionnel",
                "cost_multiplier": 2.0,
                "estimated_days": zone.estimated_days
            })
        
        # Local carriers (always available)
        carriers.append({
            "id": "local_standard",
            "name": "Livraison Standard",
            "description": "Service de livraison local",
            "cost_multiplier": 1.0,
            "estimated_days": zone.estimated_days
        })
        
        return carriers
    
    async def _geocode_address(self, address: UserAddress) -> Optional[Dict[str, float]]:
        """Geocode an address to get coordinates."""
        try:
            # Simple geocoding based on known cities
            city = address.city.lower() if address.city else ""
            
            for city_name, coords in self.major_cities.items():
                if city_name in city:
                    return {"lat": coords["lat"], "lng": coords["lng"]}
            
            return None
            
        except Exception as e:
            logger.error(f"Geocoding failed: {e}")
            return None
    
    async def _get_default_shipping_calculation(self, weight_kg: float) -> ShippingCalculation:
        """Get default shipping calculation as fallback."""
        default_zone = self._create_zone_from_config(self.default_zones[6])  # Rural area
        
        return ShippingCalculation(
            zone=default_zone,
            base_cost=default_zone.base_cost,
            weight_cost=default_zone.per_kg_cost * Decimal(str(weight_kg)),
            total_cost=default_zone.base_cost + (default_zone.per_kg_cost * Decimal(str(weight_kg))),
            estimated_delivery_days=default_zone.estimated_days,
            carrier_options=[],
            is_available=True,
            restrictions=[]
        )


# Global service instance
geography_service = GeographyService()


# Convenience functions
async def calculate_shipping_cost(
    destination: UserAddress, 
    total_weight_kg: float,
    total_value: Decimal
) -> ShippingCalculation:
    """Calculate shipping cost for destination."""
    return await geography_service.calculate_shipping_cost(destination, total_weight_kg, total_value)


async def get_delivery_options(destination: UserAddress) -> List[Dict[str, Any]]:
    """Get delivery options for destination."""
    return await geography_service.get_delivery_options(destination)


async def validate_delivery_address(address: UserAddress) -> Dict[str, Any]:
    """Validate delivery address."""
    return await geography_service.validate_delivery_address(address)
