"""
Dependencies for PromoWeb Africa FastAPI endpoints.
Handles authentication, database sessions, and common dependencies.
"""

from typing import Optional, Generator
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth import auth_service
from app.models.user import User
from app.schemas.user import TokenData
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Get current user from token (optional - returns None if not authenticated).
    Used for endpoints that work with both authenticated and anonymous users.
    """
    if not credentials:
        return None
    
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        return user
    except Exception as e:
        logger.warning(f"Optional authentication failed: {e}")
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """
    Get current authenticated user from token.
    Raises 401 if not authenticated or token is invalid.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await auth_service.get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    Additional check for user account status.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current admin user.
    Requires admin or super_admin role.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_current_super_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current super admin user.
    Requires super_admin role.
    """
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request.
    Handles X-Forwarded-For and X-Real-IP headers.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """Get user agent from request headers."""
    return request.headers.get("User-Agent", "unknown")


async def get_db_session() -> Generator[AsyncSession, None, None]:
    """
    Get database session.
    Alias for get_db dependency.
    """
    async for session in get_db():
        yield session


class RoleChecker:
    """
    Role-based access control dependency.
    Usage: Depends(RoleChecker(["admin", "super_admin"]))
    """
    
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(self.allowed_roles)}"
            )
        return current_user


class PermissionChecker:
    """
    Permission-based access control dependency.
    Checks if user has specific permissions.
    """
    
    def __init__(self, required_permission: str):
        self.required_permission = required_permission
    
    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        # For now, admin users have all permissions
        # In the future, implement granular permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {self.required_permission}"
            )
        return current_user


class ResourceOwnerChecker:
    """
    Resource ownership checker.
    Ensures user can only access their own resources.
    """
    
    def __init__(self, resource_user_id_field: str = "user_id"):
        self.resource_user_id_field = resource_user_id_field
    
    def __call__(self, resource_user_id: str, current_user: User = Depends(get_current_active_user)) -> User:
        # Admin users can access any resource
        if current_user.is_admin:
            return current_user
        
        # Check if user owns the resource
        if str(current_user.id) != resource_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only access your own resources."
            )
        return current_user


async def validate_session_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[TokenData]:
    """
    Validate session token and return token data.
    Used for session management endpoints.
    """
    if not credentials:
        return None
    
    token_data = auth_service.verify_token(credentials.credentials)
    if not token_data:
        return None
    
    # Additional validation can be added here
    # e.g., check if session exists in database
    
    return token_data


async def get_pagination_params(
    page: int = 1,
    per_page: int = 20,
    max_per_page: int = 100
) -> dict:
    """
    Get pagination parameters with validation.
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be at least 1"
        )
    
    if per_page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Items per page must be at least 1"
        )
    
    if per_page > max_per_page:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Items per page cannot exceed {max_per_page}"
        )
    
    return {
        "page": page,
        "per_page": per_page,
        "offset": (page - 1) * per_page
    }


async def validate_cart_access(
    cart_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    request: Request = None
) -> dict:
    """
    Validate cart access for both authenticated and anonymous users.
    Returns cart access context.
    """
    from app.core.database import get_db_context
    from app.models.cart import Cart
    from sqlalchemy import select
    
    async with get_db_context() as db:
        # Get cart
        cart = await db.execute(
            select(Cart).where(Cart.id == cart_id)
        )
        cart = cart.scalar_one_or_none()
        
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )
        
        # Check access permissions
        if current_user:
            # Authenticated user - check ownership
            if cart.user_id and str(cart.user_id) != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this cart"
                )
        else:
            # Anonymous user - check session
            session_id = request.headers.get("X-Session-ID") if request else None
            if cart.session_id != session_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this cart"
                )
        
        return {
            "cart": cart,
            "user": current_user,
            "is_owner": True
        }


class RateLimitChecker:
    """
    Rate limiting dependency.
    Checks if user/IP has exceeded rate limits.
    """
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    async def __call__(
        self,
        request: Request,
        current_user: Optional[User] = Depends(get_current_user_optional)
    ) -> bool:
        from app.core.redis import get_cache
        
        # Use user ID if authenticated, otherwise IP address
        identifier = str(current_user.id) if current_user else get_client_ip(request)
        cache_key = f"rate_limit:{identifier}:{request.url.path}"
        
        cache = get_cache()
        
        # Get current count
        current_count = await cache.get(cache_key)
        if current_count is None:
            current_count = 0
        else:
            current_count = int(current_count)
        
        if current_count >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                }
            )
        
        # Increment counter
        await cache.incr(cache_key)
        if current_count == 0:
            await cache.expire(cache_key, self.window_seconds)
        
        return True


# Common rate limiters
standard_rate_limit = RateLimitChecker(max_requests=100, window_seconds=3600)  # 100/hour
strict_rate_limit = RateLimitChecker(max_requests=10, window_seconds=3600)     # 10/hour
auth_rate_limit = RateLimitChecker(max_requests=5, window_seconds=300)        # 5/5min
