"""
Core configuration module for PromoWeb Africa API.
Handles all environment variables and application settings.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # =============================================================================
    # APPLICATION CONFIGURATION
    # =============================================================================
    ENVIRONMENT: str = Field(default="development", description="Environment")
    SECRET_KEY: str = Field(..., description="Secret key for security")
    DEBUG: bool = Field(default=True, description="Debug mode")
    API_VERSION: str = Field(default="v1", description="API version")
    API_PREFIX: str = Field(default="/api/v1", description="API prefix")
    
    # Server Configuration
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    RELOAD: bool = Field(default=True, description="Auto-reload on changes")

    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    DATABASE_URL: Optional[str] = Field(default=None, description="Full database URL")
    DB_HOST: str = Field(default="localhost", description="Database host")
    DB_PORT: int = Field(default=5432, description="Database port")
    DB_USER: str = Field(default="promoweb", description="Database user")
    DB_PASSWORD: str = Field(default="password_2024", description="Database password")
    DB_NAME: str = Field(default="promoweb", description="Database name")
    
    # Database Pool Configuration
    DB_POOL_SIZE: int = Field(default=20, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=0, description="Database max overflow")
    DB_ECHO: bool = Field(default=False, description="Enable SQL logging")
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        """Assemble database URL if not provided."""
        if isinstance(v, str):
            return v
        return (
            f"postgresql://{values.get('DB_USER')}:{values.get('DB_PASSWORD')}"
            f"@{values.get('DB_HOST')}:{values.get('DB_PORT')}"
            f"/{values.get('DB_NAME')}"
        )

    # =============================================================================
    # SECURITY & AUTHENTICATION
    # =============================================================================
    JWT_SECRET_KEY: str = Field(default="jwt-secret-key", description="JWT secret key")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRATION_TIME: int = Field(default=7200, description="JWT expiration (seconds)")
    JWT_REFRESH_EXPIRATION_TIME: int = Field(default=604800, description="Refresh token expiration")
    BCRYPT_ROUNDS: int = Field(default=12, description="Bcrypt hash rounds")

    # =============================================================================
    # REDIS CONFIGURATION
    # =============================================================================
    REDIS_URL: Optional[str] = Field(default=None, description="Redis URL")
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    REDIS_CACHE_TTL: int = Field(default=3600, description="Default cache TTL")
    
    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: dict) -> str:
        """Assemble Redis URL if not provided."""
        if isinstance(v, str):
            return v
        password = values.get("REDIS_PASSWORD")
        auth_part = f":{password}@" if password else ""
        return (
            f"redis://{auth_part}{values.get('REDIS_HOST')}"
            f":{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"
        )

    # =============================================================================
    # CORS CONFIGURATION
    # =============================================================================
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow credentials")
    CORS_ALLOW_METHODS: List[str] = Field(
        default=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods"
    )
    CORS_ALLOW_HEADERS: List[str] = Field(default=["*"], description="Allowed headers")

    # =============================================================================
    # FILE UPLOAD CONFIGURATION
    # =============================================================================
    MAX_FILE_SIZE: int = Field(default=10485760, description="Max file size (10MB)")
    UPLOAD_PATH: str = Field(default="./uploads", description="Upload directory")
    ALLOWED_FILE_EXTENSIONS: List[str] = Field(
        default=["jpg", "jpeg", "png", "gif", "webp", "pdf", "doc", "docx"],
        description="Allowed file extensions"
    )

    # =============================================================================
    # EMAIL CONFIGURATION
    # =============================================================================
    SMTP_HOST: str = Field(default="smtp.gmail.com", description="SMTP host")
    SMTP_PORT: int = Field(default=587, description="SMTP port")
    SMTP_USE_TLS: bool = Field(default=True, description="Use TLS")
    SMTP_USERNAME: Optional[str] = Field(default=None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP password")
    FROM_EMAIL: str = Field(default="noreply@promoweb.cm", description="From email")
    FROM_NAME: str = Field(default="PromoWeb Africa", description="From name")

    # =============================================================================
    # PAYMENT GATEWAYS
    # =============================================================================
    # Stripe
    STRIPE_PUBLISHABLE_KEY: Optional[str] = Field(default=None, description="Stripe publishable key")
    STRIPE_SECRET_KEY: Optional[str] = Field(default=None, description="Stripe secret key")
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(default=None, description="Stripe webhook secret")
    
    # Orange Money
    ORANGE_MONEY_API_URL: str = Field(
        default="https://api.orange.com/orange-money-webpay/cm/v1",
        description="Orange Money API URL"
    )
    ORANGE_MONEY_MERCHANT_KEY: Optional[str] = Field(default=None, description="Orange Money key")
    ORANGE_MONEY_CLIENT_ID: Optional[str] = Field(default=None, description="Orange Money client")
    ORANGE_MONEY_CLIENT_SECRET: Optional[str] = Field(default=None, description="Orange Money secret")
    
    # MTN Mobile Money
    MTN_MOMO_API_URL: str = Field(
        default="https://sandbox.momodeveloper.mtn.com",
        description="MTN MoMo API URL"
    )
    MTN_MOMO_SUBSCRIPTION_KEY: Optional[str] = Field(default=None, description="MTN subscription key")
    MTN_MOMO_API_USER_ID: Optional[str] = Field(default=None, description="MTN API user ID")
    MTN_MOMO_API_KEY: Optional[str] = Field(default=None, description="MTN API key")

    # =============================================================================
    # EXTERNAL APIS
    # =============================================================================
    EXCHANGE_RATE_API_URL: str = Field(
        default="https://api.exchangerate-api.com/v4/latest/EUR",
        description="Exchange rate API"
    )
    EXCHANGE_RATE_API_KEY: Optional[str] = Field(default=None, description="Exchange rate API key")
    
    GOOGLE_MERCHANT_API_URL: str = Field(
        default="https://shoppingcontent.googleapis.com/content/v2.1",
        description="Google Merchant API"
    )
    GOOGLE_MERCHANT_ID: Optional[str] = Field(default=None, description="Google Merchant ID")
    GOOGLE_API_KEY: Optional[str] = Field(default=None, description="Google API key")

    # =============================================================================
    # SMS & NOTIFICATIONS
    # =============================================================================
    TWILIO_ACCOUNT_SID: Optional[str] = Field(default=None, description="Twilio account SID")
    TWILIO_AUTH_TOKEN: Optional[str] = Field(default=None, description="Twilio auth token")
    TWILIO_PHONE_NUMBER: Optional[str] = Field(default=None, description="Twilio phone number")
    
    AFRICASTALKING_USERNAME: str = Field(default="sandbox", description="Africa's Talking username")
    AFRICASTALKING_API_KEY: Optional[str] = Field(default=None, description="Africa's Talking API key")

    # =============================================================================
    # BUSINESS CONFIGURATION
    # =============================================================================
    DEFAULT_DEPOSIT_PERCENTAGE: int = Field(default=30, description="Default deposit percentage")
    DEFAULT_MARGIN_PERCENTAGE: int = Field(default=35, description="Default margin percentage")
    DEFAULT_SHIPPING_COST: int = Field(default=2000, description="Default shipping cost (XAF)")
    WEIGHT_RATE_PER_KG: int = Field(default=500, description="Weight rate per kg (XAF)")
    FREE_SHIPPING_THRESHOLD: int = Field(default=50000, description="Free shipping threshold (XAF)")
    
    BASE_CURRENCY: str = Field(default="EUR", description="Base currency")
    TARGET_CURRENCY: str = Field(default="XAF", description="Target currency")
    PRICE_ROUNDING_THRESHOLD: int = Field(default=100, description="Price rounding threshold")

    # =============================================================================
    # CELERY CONFIGURATION
    # =============================================================================
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", description="Celery broker")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/1", description="Celery backend")
    CELERY_TASK_SERIALIZER: str = Field(default="json", description="Task serializer")
    CELERY_RESULT_SERIALIZER: str = Field(default="json", description="Result serializer")
    CELERY_ACCEPT_CONTENT: List[str] = Field(default=["json"], description="Accept content")
    CELERY_TIMEZONE: str = Field(default="Africa/Douala", description="Celery timezone")

    # =============================================================================
    # LOGGING CONFIGURATION
    # =============================================================================
    LOG_LEVEL: str = Field(default="INFO", description="Log level")
    LOG_FILE: str = Field(default="logs/app.log", description="Log file path")
    LOG_MAX_SIZE: int = Field(default=10485760, description="Log max size")
    LOG_BACKUP_COUNT: int = Field(default=5, description="Log backup count")

    # =============================================================================
    # MONITORING
    # =============================================================================
    SENTRY_DSN: Optional[str] = Field(default=None, description="Sentry DSN")
    PROMETHEUS_METRICS_ENABLED: bool = Field(default=True, description="Enable Prometheus")

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing."""
        return self.ENVIRONMENT.lower() == "testing"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
