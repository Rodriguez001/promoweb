"""
User schemas for PromoWeb Africa.
Pydantic models for user data validation and serialization.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from decimal import Decimal


# Base schemas
class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    """Schema for user updates."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(UserBase):
    """Schema for user response."""
    id: str
    role: str
    is_active: bool
    email_verified: bool
    phone_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserProfile(UserResponse):
    """Extended user profile with additional information."""
    full_name: str
    is_admin: bool
    addresses: List["UserAddressResponse"] = []
    preferences: Optional["UserPreferenceResponse"] = None


# Address schemas
class UserAddressBase(BaseModel):
    """Base address schema."""
    name: str = Field(..., min_length=1, max_length=100)
    street_address: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    country: str = Field(default="CM", max_length=2)
    is_default: bool = Field(default=False)


class UserAddressCreate(UserAddressBase):
    """Schema for creating user address."""
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class UserAddressUpdate(BaseModel):
    """Schema for updating user address."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    street_address: Optional[str] = Field(None, min_length=1)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    is_default: Optional[bool] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class UserAddressResponse(UserAddressBase):
    """Schema for address response."""
    id: str
    full_address: str
    coordinates: Optional[tuple[float, float]]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Preference schemas
class UserPreferenceBase(BaseModel):
    """Base preference schema."""
    language: str = Field(default="fr", regex=r"^(fr|en)$")
    currency: str = Field(default="XAF", regex=r"^(XAF|EUR)$")
    timezone: str = Field(default="Africa/Douala")
    email_notifications: bool = Field(default=True)
    sms_notifications: bool = Field(default=True)
    marketing_emails: bool = Field(default=False)
    items_per_page: int = Field(default=20, ge=10, le=100)
    theme: str = Field(default="light", regex=r"^(light|dark|auto)$")


class UserPreferenceUpdate(BaseModel):
    """Schema for updating user preferences."""
    language: Optional[str] = Field(None, regex=r"^(fr|en)$")
    currency: Optional[str] = Field(None, regex=r"^(XAF|EUR)$")
    timezone: Optional[str] = None
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    items_per_page: Optional[int] = Field(None, ge=10, le=100)
    theme: Optional[str] = Field(None, regex=r"^(light|dark|auto)$")


class UserPreferenceResponse(UserPreferenceBase):
    """Schema for preference response."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Authentication schemas
class Token(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """Token payload data."""
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class RefreshToken(BaseModel):
    """Refresh token request."""
    refresh_token: str


# Password reset schemas
class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr


class PasswordReset(BaseModel):
    """Password reset with token."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class PasswordChange(BaseModel):
    """Password change for authenticated users."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


# Email verification schemas
class EmailVerificationRequest(BaseModel):
    """Email verification request."""
    email: EmailStr


class EmailVerification(BaseModel):
    """Email verification with token."""
    token: str


# Session schemas
class UserSessionResponse(BaseModel):
    """User session response."""
    id: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_info: Optional[str]
    is_active: bool
    last_activity: datetime
    expires_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


# Statistics schemas
class UserStats(BaseModel):
    """User statistics."""
    total_orders: int
    total_spent: Decimal
    average_order_value: Decimal
    favorite_categories: List[str]
    last_order_date: Optional[datetime]
    loyalty_points: int = 0


# Forward references
UserProfile.model_rebuild()
UserAddressResponse.model_rebuild()
UserPreferenceResponse.model_rebuild()
