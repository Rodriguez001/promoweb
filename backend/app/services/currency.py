"""
Currency conversion service for PromoWeb Africa.
Handles EUR to XAF conversion with caching and exchange rate API integration.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any
from dataclasses import dataclass

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_context
from app.core.redis import get_cache
from app.models.payment import ExchangeRate

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class ConversionResult:
    """Result of currency conversion."""
    amount_eur: Decimal
    amount_xaf: Decimal
    exchange_rate: Decimal
    rate_date: datetime
    source: str


class CurrencyService:
    """Service for handling currency conversions."""
    
    def __init__(self):
        self.cache_ttl = 3600  # 1 hour cache
        self.exchange_apis = [
            {
                "name": "exchangerate-api",
                "url": "https://api.exchangerate-api.com/v4/latest/EUR",
                "key_path": ["rates", "XAF"]
            },
            {
                "name": "fixer",
                "url": f"http://data.fixer.io/api/latest?access_key={settings.FIXER_API_KEY}&base=EUR&symbols=XAF",
                "key_path": ["rates", "XAF"]
            }
        ]
    
    async def get_exchange_rate(self, force_refresh: bool = False) -> Decimal:
        """
        Get current EUR to XAF exchange rate.
        
        Args:
            force_refresh: Force fetching fresh rate from API
            
        Returns:
            Exchange rate as Decimal
        """
        # Try cache first unless forced refresh
        if not force_refresh:
            cached_rate = await self._get_cached_rate()
            if cached_rate:
                return cached_rate
        
        # Fetch from APIs
        rate = await self._fetch_rate_from_apis()
        if rate:
            # Cache the rate
            await self._cache_rate(rate)
            # Store in database
            await self._store_rate_in_db(rate)
            return rate
        
        # Fallback to database
        db_rate = await self._get_rate_from_db()
        if db_rate:
            return db_rate
        
        # Final fallback - default rate
        logger.warning("Using fallback exchange rate")
        return Decimal('656.0')  # Approximate EUR to XAF rate
    
    async def convert_eur_to_xaf(
        self, 
        amount_eur: Decimal, 
        margin_percentage: Decimal = Decimal('0'),
        round_to_hundred: bool = True
    ) -> ConversionResult:
        """
        Convert EUR amount to XAF with margin and rounding.
        
        Args:
            amount_eur: Amount in EUR
            margin_percentage: Margin percentage to add
            round_to_hundred: Round to nearest 100 XAF
            
        Returns:
            ConversionResult with all conversion details
        """
        try:
            # Get current exchange rate
            rate = await self.get_exchange_rate()
            
            # Calculate base XAF amount
            base_xaf = amount_eur * rate
            
            # Apply margin
            if margin_percentage > 0:
                base_xaf = base_xaf * (1 + margin_percentage / 100)
            
            # Round to nearest 100 XAF if requested
            if round_to_hundred:
                final_xaf = Decimal(int(base_xaf / 100) * 100)
            else:
                final_xaf = base_xaf.quantize(Decimal('0.01'))
            
            return ConversionResult(
                amount_eur=amount_eur,
                amount_xaf=final_xaf,
                exchange_rate=rate,
                rate_date=datetime.utcnow(),
                source="api"
            )
            
        except Exception as e:
            logger.error(f"Currency conversion failed: {e}")
            raise
    
    async def convert_xaf_to_eur(self, amount_xaf: Decimal) -> ConversionResult:
        """
        Convert XAF amount to EUR.
        
        Args:
            amount_xaf: Amount in XAF
            
        Returns:
            ConversionResult with conversion details
        """
        try:
            rate = await self.get_exchange_rate()
            amount_eur = (amount_xaf / rate).quantize(Decimal('0.01'))
            
            return ConversionResult(
                amount_eur=amount_eur,
                amount_xaf=amount_xaf,
                exchange_rate=rate,
                rate_date=datetime.utcnow(),
                source="api"
            )
            
        except Exception as e:
            logger.error(f"Currency conversion failed: {e}")
            raise
    
    async def get_conversion_history(self, days: int = 30) -> list[Dict[str, Any]]:
        """Get exchange rate history from database."""
        try:
            async with get_db_context() as db:
                since_date = datetime.utcnow() - timedelta(days=days)
                
                result = await db.execute(
                    select(ExchangeRate)
                    .where(ExchangeRate.date >= since_date)
                    .order_by(ExchangeRate.date.desc())
                )
                
                rates = result.scalars().all()
                
                return [
                    {
                        "date": rate.date.isoformat(),
                        "rate": float(rate.rate),
                        "source": rate.source
                    }
                    for rate in rates
                ]
                
        except Exception as e:
            logger.error(f"Failed to get conversion history: {e}")
            return []
    
    async def _get_cached_rate(self) -> Optional[Decimal]:
        """Get exchange rate from Redis cache."""
        try:
            cache = await get_cache()
            cached_data = await cache.get("exchange_rate:EUR:XAF")
            if cached_data:
                import json
                data = json.loads(cached_data)
                return Decimal(str(data['rate']))
        except Exception as e:
            logger.error(f"Failed to get cached rate: {e}")
        return None
    
    async def _cache_rate(self, rate: Decimal) -> None:
        """Cache exchange rate in Redis."""
        try:
            cache = await get_cache()
            import json
            cache_data = {
                "rate": str(rate),
                "timestamp": datetime.utcnow().isoformat()
            }
            await cache.setex(
                "exchange_rate:EUR:XAF", 
                self.cache_ttl,
                json.dumps(cache_data)
            )
        except Exception as e:
            logger.error(f"Failed to cache rate: {e}")
    
    async def _fetch_rate_from_apis(self) -> Optional[Decimal]:
        """Fetch exchange rate from external APIs."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            for api in self.exchange_apis:
                try:
                    logger.info(f"Fetching rate from {api['name']}")
                    response = await client.get(api['url'])
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    # Navigate to rate using key_path
                    rate_value = data
                    for key in api['key_path']:
                        rate_value = rate_value[key]
                    
                    rate = Decimal(str(rate_value))
                    logger.info(f"Got rate {rate} from {api['name']}")
                    return rate
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch from {api['name']}: {e}")
                    continue
        
        return None
    
    async def _store_rate_in_db(self, rate: Decimal) -> None:
        """Store exchange rate in database."""
        try:
            async with get_db_context() as db:
                # Check if rate for today already exists
                today = datetime.utcnow().date()
                existing = await db.execute(
                    select(ExchangeRate).where(
                        ExchangeRate.from_currency == "EUR",
                        ExchangeRate.to_currency == "XAF",
                        ExchangeRate.date >= today
                    )
                )
                
                if existing.scalar_one_or_none():
                    # Update existing rate
                    await db.execute(
                        update(ExchangeRate)
                        .where(
                            ExchangeRate.from_currency == "EUR",
                            ExchangeRate.to_currency == "XAF",
                            ExchangeRate.date >= today
                        )
                        .values(rate=rate, updated_at=datetime.utcnow())
                    )
                else:
                    # Create new rate record
                    new_rate = ExchangeRate(
                        from_currency="EUR",
                        to_currency="XAF",
                        rate=rate,
                        date=datetime.utcnow(),
                        source="api"
                    )
                    db.add(new_rate)
                
                await db.commit()
                logger.info(f"Stored exchange rate in database: {rate}")
                
        except Exception as e:
            logger.error(f"Failed to store rate in database: {e}")
    
    async def _get_rate_from_db(self) -> Optional[Decimal]:
        """Get latest exchange rate from database."""
        try:
            async with get_db_context() as db:
                result = await db.execute(
                    select(ExchangeRate)
                    .where(
                        ExchangeRate.from_currency == "EUR",
                        ExchangeRate.to_currency == "XAF"
                    )
                    .order_by(ExchangeRate.date.desc())
                    .limit(1)
                )
                
                rate_record = result.scalar_one_or_none()
                if rate_record:
                    logger.info(f"Using database rate: {rate_record.rate}")
                    return rate_record.rate
                    
        except Exception as e:
            logger.error(f"Failed to get rate from database: {e}")
        
        return None


# Global service instance
currency_service = CurrencyService()


# Convenience functions
async def convert_eur_to_xaf(
    amount_eur: Decimal, 
    margin_percentage: Decimal = Decimal('0')
) -> ConversionResult:
    """Convert EUR to XAF with margin."""
    return await currency_service.convert_eur_to_xaf(amount_eur, margin_percentage)


async def convert_xaf_to_eur(amount_xaf: Decimal) -> ConversionResult:
    """Convert XAF to EUR."""
    return await currency_service.convert_xaf_to_eur(amount_xaf)


async def get_current_exchange_rate() -> Decimal:
    """Get current EUR to XAF exchange rate."""
    return await currency_service.get_exchange_rate()


# Background task for updating exchange rates
async def update_exchange_rates():
    """Background task to update exchange rates periodically."""
    try:
        await currency_service.get_exchange_rate(force_refresh=True)
        logger.info("Exchange rates updated successfully")
    except Exception as e:
        logger.error(f"Failed to update exchange rates: {e}")
