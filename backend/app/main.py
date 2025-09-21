"""
PromoWeb Africa - Main FastAPI Application
E-commerce platform for European products in Cameroon
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import time
import logging

from app.core.config import get_settings
from app.core.database import create_db_and_tables
from app.core.logging import setup_logging
from app.api.v1.api import api_router
from app.core.middleware import (
    ProcessTimeMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("🚀 Starting PromoWeb Africa API...")
    
    # Initialize database
    await create_db_and_tables()
    logger.info("✅ Database initialized")
    
    # Initialize Redis connection
    from app.core.redis import init_redis
    await init_redis()
    logger.info("✅ Redis initialized")
    
    # Start background tasks
    logger.info("✅ PromoWeb API started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down PromoWeb Africa API...")
    
    # Cleanup Redis
    from app.core.redis import close_redis
    await close_redis()
    logger.info("✅ Redis connection closed")
    
    logger.info("✅ PromoWeb API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="PromoWeb Africa API",
    description="""
    🛒 **PromoWeb Africa E-commerce API**
    
    Plateforme e-commerce spécialisée dans les produits européens 
    de parapharmacie, beauté, bien-être, et livres à destination 
    des consommateurs camerounais.
    
    ## Fonctionnalités principales
    
    * **Catalogue produits** - Gestion complète avec sync Google Merchant
    * **Commandes & Paiements** - Acompte 30% + Mobile Money (Orange/MTN)
    * **Livraison géospatiale** - Calcul automatique avec PostGIS
    * **Authentification JWT** - Sécurisée avec refresh tokens
    * **Analytics** - Suivi complet des performances
    
    ## Technologies
    
    * **FastAPI** - Framework moderne et performant
    * **PostgreSQL + PostGIS** - Base de données géospatiale
    * **SQLAlchemy** - ORM avancé avec support async
    * **Redis** - Cache haute performance
    * **Celery** - Tâches asynchrones
    """,
    version="1.0.0",
    contact={
        "name": "PromoWeb Africa Team",
        "email": "admin@promoweb.cm",
        "url": "https://promoweb.cm",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://promoweb.cm/license",
    },
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check and monitoring",
        },
        {
            "name": "auth",
            "description": "Authentication and authorization",
        },
        {
            "name": "users",
            "description": "User management",
        },
        {
            "name": "products",
            "description": "Product catalog management",
        },
        {
            "name": "categories",
            "description": "Product categories",
        },
        {
            "name": "cart",
            "description": "Shopping cart operations",
        },
        {
            "name": "orders",
            "description": "Order management",
        },
        {
            "name": "payments",
            "description": "Payment processing (Stripe, Mobile Money)",
        },
        {
            "name": "shipping",
            "description": "Shipping and delivery management",
        },
        {
            "name": "analytics",
            "description": "Analytics and reporting",
        },
        {
            "name": "admin",
            "description": "Administrative operations",
        },
    ],
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add middleware
# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Trusted hosts
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["promoweb.cm", "*.promoweb.cm", "localhost", "127.0.0.1"]
    )

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Rate limiting
app.add_middleware(RateLimitMiddleware)

# Process time
app.add_middleware(ProcessTimeMiddleware)


# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="static")


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Resource not found",
            "path": str(request.url.path),
            "method": request.method,
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "path": str(request.url.path),
            "method": request.method,
        }
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns basic application status and dependencies health.
    """
    from app.core.database import get_db_status
    from app.core.redis import get_redis_status
    
    db_status = await get_db_status()
    redis_status = await get_redis_status()
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "services": {
            "database": db_status,
            "redis": redis_status,
        }
    }


@app.get("/", tags=["health"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "🛒 PromoWeb Africa API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "environment": settings.ENVIRONMENT,
    }


# Include API routes
app.include_router(api_router, prefix=settings.API_PREFIX)


# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD and settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )
