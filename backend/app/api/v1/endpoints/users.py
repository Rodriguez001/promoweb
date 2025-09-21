"""
User management endpoints for PromoWeb Africa.
Handles user profiles, addresses, preferences, and account management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.api.dependencies import (
    get_current_user, get_current_admin_user, get_pagination_params,
    ResourceOwnerChecker, get_db_session
)
from app.models.user import User, UserAddress, UserPreference, UserSession
from app.schemas.user import (
    UserResponse, UserProfile, UserUpdate, UserAddressCreate, 
    UserAddressUpdate, UserAddressResponse, UserPreferenceUpdate,
    UserPreferenceResponse, UserSessionResponse, UserStats
)
from app.schemas.common import BaseResponse, PaginatedResponse
from app.core.database import get_db_context
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's complete profile.
    
    Returns user information with addresses and preferences.
    """
    async with get_db_context() as db:
        # Load user with all related data
        user = await db.execute(
            select(User)
            .where(User.id == current_user.id)
            .options(
                selectinload(User.addresses),
                selectinload(User.preferences)
            )
        )
        user = user.scalar_one()
        
        return UserProfile(
            **user.__dict__,
            full_name=user.full_name,
            is_admin=user.is_admin,
            addresses=[UserAddressResponse(**addr.__dict__) for addr in user.addresses],
            preferences=UserPreferenceResponse(**user.preferences[0].__dict__) if user.preferences else None
        )


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update current user's profile information.
    
    - **first_name**: User's first name
    - **last_name**: User's last name  
    - **phone**: Phone number
    """
    try:
        async with get_db_context() as db:
            # Update user fields
            update_data = user_update.dict(exclude_unset=True)
            if update_data:
                await db.execute(
                    update(User)
                    .where(User.id == current_user.id)
                    .values(**update_data, updated_at=datetime.utcnow())
                )
                await db.commit()
                
                # Get updated user
                user = await db.get(User, current_user.id)
                
                logger.info(f"User profile updated: {user.email}")
                return user
            
            return current_user
            
    except Exception as e:
        logger.error(f"Profile update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.get("/addresses", response_model=List[UserAddressResponse])
async def get_user_addresses(current_user: User = Depends(get_current_user)):
    """Get all addresses for current user."""
    async with get_db_context() as db:
        addresses = await db.execute(
            select(UserAddress)
            .where(UserAddress.user_id == current_user.id)
            .order_by(UserAddress.is_default.desc(), UserAddress.created_at.desc())
        )
        return addresses.scalars().all()


@router.post("/addresses", response_model=UserAddressResponse, status_code=status.HTTP_201_CREATED)
async def create_user_address(
    address_data: UserAddressCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create new address for current user.
    
    - **name**: Address name/label (e.g., "Home", "Office")
    - **street_address**: Street address
    - **city**: City name
    - **region**: Region/state (optional)
    - **postal_code**: Postal code (optional)
    - **country**: Country code (default: CM)
    - **is_default**: Set as default address
    - **latitude**: GPS latitude (optional)
    - **longitude**: GPS longitude (optional)
    """
    try:
        async with get_db_context() as db:
            # If this is set as default, unset other defaults
            if address_data.is_default:
                await db.execute(
                    update(UserAddress)
                    .where(UserAddress.user_id == current_user.id)
                    .values(is_default=False)
                )
            
            # Create address
            address = UserAddress(
                user_id=current_user.id,
                **address_data.dict(exclude={'latitude', 'longitude'})
            )
            
            # Add GPS coordinates if provided
            if address_data.latitude and address_data.longitude:
                from geoalchemy2 import WKTElement
                address.location = WKTElement(
                    f'POINT({address_data.longitude} {address_data.latitude})',
                    srid=4326
                )
            
            db.add(address)
            await db.commit()
            await db.refresh(address)
            
            logger.info(f"Address created for user: {current_user.email}")
            return address
            
    except Exception as e:
        logger.error(f"Address creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Address creation failed"
        )


@router.put("/addresses/{address_id}", response_model=UserAddressResponse)
async def update_user_address(
    address_id: str,
    address_update: UserAddressUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user address."""
    try:
        async with get_db_context() as db:
            # Get address and verify ownership
            address = await db.execute(
                select(UserAddress).where(
                    UserAddress.id == address_id,
                    UserAddress.user_id == current_user.id
                )
            )
            address = address.scalar_one_or_none()
            
            if not address:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Address not found"
                )
            
            # If setting as default, unset other defaults
            if address_update.is_default:
                await db.execute(
                    update(UserAddress)
                    .where(
                        UserAddress.user_id == current_user.id,
                        UserAddress.id != address_id
                    )
                    .values(is_default=False)
                )
            
            # Update address
            update_data = address_update.dict(exclude_unset=True, exclude={'latitude', 'longitude'})
            if update_data:
                await db.execute(
                    update(UserAddress)
                    .where(UserAddress.id == address_id)
                    .values(**update_data)
                )
            
            # Update GPS coordinates if provided
            if address_update.latitude and address_update.longitude:
                from geoalchemy2 import WKTElement
                address.location = WKTElement(
                    f'POINT({address_update.longitude} {address_update.latitude})',
                    srid=4326
                )
            
            await db.commit()
            await db.refresh(address)
            
            logger.info(f"Address updated for user: {current_user.email}")
            return address
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Address update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Address update failed"
        )


@router.delete("/addresses/{address_id}", response_model=BaseResponse)
async def delete_user_address(
    address_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete user address."""
    try:
        async with get_db_context() as db:
            # Get address and verify ownership
            address = await db.execute(
                select(UserAddress).where(
                    UserAddress.id == address_id,
                    UserAddress.user_id == current_user.id
                )
            )
            address = address.scalar_one_or_none()
            
            if not address:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Address not found"
                )
            
            await db.delete(address)
            await db.commit()
            
            logger.info(f"Address deleted for user: {current_user.email}")
            return BaseResponse(message="Address deleted successfully")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Address deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Address deletion failed"
        )


@router.get("/preferences", response_model=UserPreferenceResponse)
async def get_user_preferences(current_user: User = Depends(get_current_user)):
    """Get current user's preferences."""
    async with get_db_context() as db:
        preferences = await db.execute(
            select(UserPreference).where(UserPreference.user_id == current_user.id)
        )
        preferences = preferences.scalar_one_or_none()
        
        if not preferences:
            # Create default preferences
            preferences = UserPreference(user_id=current_user.id)
            db.add(preferences)
            await db.commit()
            await db.refresh(preferences)
        
        return preferences


@router.put("/preferences", response_model=UserPreferenceResponse)
async def update_user_preferences(
    preferences_update: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update current user's preferences."""
    try:
        async with get_db_context() as db:
            # Get or create preferences
            preferences = await db.execute(
                select(UserPreference).where(UserPreference.user_id == current_user.id)
            )
            preferences = preferences.scalar_one_or_none()
            
            if not preferences:
                preferences = UserPreference(user_id=current_user.id, **preferences_update.dict(exclude_unset=True))
                db.add(preferences)
            else:
                update_data = preferences_update.dict(exclude_unset=True)
                if update_data:
                    await db.execute(
                        update(UserPreference)
                        .where(UserPreference.user_id == current_user.id)
                        .values(**update_data, updated_at=datetime.utcnow())
                    )
            
            await db.commit()
            await db.refresh(preferences)
            
            logger.info(f"Preferences updated for user: {current_user.email}")
            return preferences
            
    except Exception as e:
        logger.error(f"Preferences update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Preferences update failed"
        )


@router.get("/sessions", response_model=List[UserSessionResponse])
async def get_user_sessions(current_user: User = Depends(get_current_user)):
    """Get all active sessions for current user."""
    async with get_db_context() as db:
        sessions = await db.execute(
            select(UserSession)
            .where(
                UserSession.user_id == current_user.id,
                UserSession.is_active == True
            )
            .order_by(UserSession.last_activity.desc())
        )
        return sessions.scalars().all()


@router.delete("/sessions/{session_id}", response_model=BaseResponse)
async def revoke_user_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Revoke a specific user session."""
    try:
        async with get_db_context() as db:
            result = await db.execute(
                update(UserSession)
                .where(
                    UserSession.id == session_id,
                    UserSession.user_id == current_user.id
                )
                .values(is_active=False)
            )
            await db.commit()
            
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            
            logger.info(f"Session revoked for user: {current_user.email}")
            return BaseResponse(message="Session revoked successfully")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session revocation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session revocation failed"
        )


@router.get("/stats", response_model=UserStats)
async def get_user_stats(current_user: User = Depends(get_current_user)):
    """Get user statistics and metrics."""
    try:
        async with get_db_context() as db:
            from app.models.order import Order
            from sqlalchemy import func
            
            # Get order statistics
            order_stats = await db.execute(
                select(
                    func.count(Order.id).label('total_orders'),
                    func.coalesce(func.sum(Order.total_amount), 0).label('total_spent'),
                    func.coalesce(func.avg(Order.total_amount), 0).label('average_order_value'),
                    func.max(Order.created_at).label('last_order_date')
                )
                .where(
                    Order.user_id == current_user.id,
                    Order.status.in_(['completed', 'delivered', 'paid_full'])
                )
            )
            stats = order_stats.first()
            
            # Get favorite categories (placeholder)
            favorite_categories = ["Livres", "Électronique", "Mode"]
            
            return UserStats(
                total_orders=stats.total_orders or 0,
                total_spent=stats.total_spent or 0,
                average_order_value=stats.average_order_value or 0,
                favorite_categories=favorite_categories,
                last_order_date=stats.last_order_date,
                loyalty_points=0  # Placeholder for future loyalty system
            )
            
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )


# Admin endpoints
@router.get("/admin/users", response_model=PaginatedResponse[UserResponse])
async def list_users(
    pagination: dict = Depends(get_pagination_params),
    admin_user: User = Depends(get_current_admin_user),
    search: Optional[str] = Query(None, description="Search by name or email"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """
    List all users (admin only).
    
    Supports pagination, search, and filtering.
    """
    try:
        async with get_db_context() as db:
            # Build query
            query = select(User)
            
            # Apply filters
            if search:
                search_term = f"%{search}%"
                query = query.where(
                    (User.first_name.ilike(search_term)) |
                    (User.last_name.ilike(search_term)) |
                    (User.email.ilike(search_term))
                )
            
            if role:
                query = query.where(User.role == role)
            
            if is_active is not None:
                query = query.where(User.is_active == is_active)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = await db.execute(count_query)
            total = total.scalar()
            
            # Get paginated results
            users = await db.execute(
                query.offset(pagination['offset'])
                .limit(pagination['per_page'])
                .order_by(User.created_at.desc())
            )
            
            return PaginatedResponse.create(
                items=users.scalars().all(),
                page=pagination['page'],
                per_page=pagination['per_page'],
                total=total
            )
            
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/admin/users/{user_id}", response_model=UserProfile)
async def get_user_by_id(
    user_id: str,
    admin_user: User = Depends(get_current_admin_user)
):
    """Get user by ID (admin only)."""
    async with get_db_context() as db:
        user = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.addresses),
                selectinload(User.preferences)
            )
        )
        user = user.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserProfile(
            **user.__dict__,
            full_name=user.full_name,
            is_admin=user.is_admin,
            addresses=[UserAddressResponse(**addr.__dict__) for addr in user.addresses],
            preferences=UserPreferenceResponse(**user.preferences[0].__dict__) if user.preferences else None
        )


@router.put("/admin/users/{user_id}/status", response_model=BaseResponse)
async def update_user_status(
    user_id: str,
    is_active: bool,
    admin_user: User = Depends(get_current_admin_user)
):
    """Update user active status (admin only)."""
    try:
        async with get_db_context() as db:
            result = await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(is_active=is_active, updated_at=datetime.utcnow())
            )
            await db.commit()
            
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            status_text = "activated" if is_active else "deactivated"
            logger.info(f"User {status_text} by admin: {user_id}")
            
            return BaseResponse(message=f"User {status_text} successfully")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user status"
        )
