"""
Database configuration and connection management for PromoWeb Africa.
Handles SQLAlchemy setup with PostgreSQL + PostGIS support.
"""

import logging
from typing import AsyncGenerator, Dict, Any
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Database URL conversion for async
DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine
async_engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections every hour
    echo=settings.DB_ECHO,
    future=True,
)

# Create sync engine for migrations
sync_engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DB_ECHO,
    future=True,
)

# Session factories
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context():
    """
    Context manager for database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_db_and_tables() -> None:
    """
    Create database tables if they don't exist.
    This is called on application startup.
    """
    try:
        # Import all models to ensure they are registered with Base
        from app.models import (  # noqa: F401
            user,
            product,
            category,
            cart,
            order,
            payment,
            shipping,
            promotion,
            analytics,
        )
        
        logger.info("Creating database tables...")
        
        async with async_engine.begin() as conn:
            # Enable PostGIS extension if not exists
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("✅ Database tables created successfully")
        
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        raise


async def get_db_status() -> Dict[str, Any]:
    """
    Get database connection status for health checks.
    
    Returns:
        Dict[str, Any]: Database status information
    """
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as healthy, version() as version"))
            row = result.fetchone()
            
            if row:
                return {
                    "status": "healthy",
                    "version": row.version,
                    "connection_pool": {
                        "size": async_engine.pool.size(),
                        "checked_in": async_engine.pool.checkedin(),
                        "checked_out": async_engine.pool.checkedout(),
                    }
                }
            else:
                return {"status": "unhealthy", "error": "No response from database"}
                
    except SQLAlchemyError as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"Unexpected error in database health check: {e}")
        return {
            "status": "unhealthy",
            "error": "Unexpected error",
        }


async def close_db_connections() -> None:
    """Close all database connections."""
    try:
        await async_engine.dispose()
        sync_engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database connections: {e}")


class DatabaseManager:
    """Database manager for handling connections and transactions."""
    
    def __init__(self):
        self.engine = async_engine
        self.session_factory = AsyncSessionLocal
    
    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> Any:
        """
        Execute a raw SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        async with self.session_factory() as session:
            try:
                result = await session.execute(text(query), params or {})
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
    
    async def execute_procedure(self, procedure_name: str, params: Dict[str, Any] = None) -> Any:
        """
        Execute a stored procedure.
        
        Args:
            procedure_name: Name of the stored procedure
            params: Procedure parameters
            
        Returns:
            Procedure result
        """
        query = f"CALL {procedure_name}({', '.join([f':{k}' for k in (params or {}).keys()])})"
        return await self.execute_query(query, params)
    
    @asynccontextmanager
    async def transaction(self):
        """
        Context manager for database transactions.
        
        Yields:
            AsyncSession: Database session within transaction
        """
        async with self.session_factory() as session:
            async with session.begin():
                try:
                    yield session
                except Exception:
                    await session.rollback()
                    raise


# Global database manager instance
db_manager = DatabaseManager()
