"""
Authentication endpoints for PromoWeb Africa.
Handles user registration, login, token refresh, and password management.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials

from app.api.dependencies import (
    get_current_user, get_current_user_optional, get_client_ip, 
    get_user_agent, auth_rate_limit, security
)
from app.services.auth import auth_service
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, Token, RefreshToken,
    PasswordResetRequest, PasswordReset, PasswordChange,
    EmailVerificationRequest, EmailVerification
)
from app.schemas.common import BaseResponse, ErrorResponse
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    _: bool = Depends(auth_rate_limit)
):
    """
    Register a new user account.
    
    - **email**: Valid email address (will be used for login)
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)
    - **confirm_password**: Must match password
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **phone**: Optional phone number
    """
    try:
        # Create user
        user = await auth_service.create_user(user_data)
        
        # Send email verification in background
        background_tasks.add_task(send_email_verification, user.id)
        
        logger.info(f"User registered successfully: {user.email}")
        
        return BaseResponse(
            message="Account created successfully. Please check your email to verify your account.",
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    request: Request,
    _: bool = Depends(auth_rate_limit)
):
    """
    Authenticate user and return access/refresh tokens.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns JWT tokens for API authentication.
    """
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(
            user_credentials.email, 
            user_credentials.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get client info
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        # Create session and tokens
        access_token, refresh_token = await auth_service.create_user_session(
            user, ip_address, user_agent
        )
        
        logger.info(f"User logged in successfully: {user.email}")
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=auth_service.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshToken,
    _: bool = Depends(auth_rate_limit)
):
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid refresh token
    
    Returns new access and refresh tokens.
    """
    try:
        tokens = await auth_service.refresh_token(refresh_data.refresh_token)
        
        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token, new_refresh_token = tokens
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=auth_service.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed. Please try again."
        )


@router.post("/logout", response_model=BaseResponse)
async def logout(
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Logout user and revoke current session.
    
    Requires valid authentication token.
    """
    try:
        # Revoke current session
        success = await auth_service.revoke_session(
            str(current_user.id), 
            credentials.credentials
        )
        
        if not success:
            logger.warning(f"Failed to revoke session for user: {current_user.email}")
        
        logger.info(f"User logged out: {current_user.email}")
        
        return BaseResponse(message="Logged out successfully")
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed. Please try again."
        )


@router.post("/logout-all", response_model=BaseResponse)
async def logout_all(current_user: User = Depends(get_current_user)):
    """
    Logout user from all devices/sessions.
    
    Revokes all active sessions for the user.
    """
    try:
        revoked_count = await auth_service.revoke_all_sessions(str(current_user.id))
        
        logger.info(f"User logged out from all sessions: {current_user.email} ({revoked_count} sessions)")
        
        return BaseResponse(
            message=f"Logged out from all devices successfully ({revoked_count} sessions revoked)"
        )
        
    except Exception as e:
        logger.error(f"Logout all failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed. Please try again."
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Returns user profile data.
    """
    return current_user


@router.post("/password/forgot", response_model=BaseResponse)
async def forgot_password(
    request_data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    _: bool = Depends(auth_rate_limit)
):
    """
    Request password reset email.
    
    - **email**: User's email address
    
    Sends password reset email if account exists.
    """
    try:
        token = await auth_service.create_password_reset_token(request_data.email)
        
        if token:
            # Send reset email in background
            background_tasks.add_task(send_password_reset_email, request_data.email, token)
            logger.info(f"Password reset requested for: {request_data.email}")
        else:
            # Don't reveal if email exists or not for security
            logger.warning(f"Password reset requested for non-existent email: {request_data.email}")
        
        return BaseResponse(
            message="If an account with this email exists, you will receive password reset instructions."
        )
        
    except Exception as e:
        logger.error(f"Password reset request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed. Please try again."
        )


@router.post("/password/reset", response_model=BaseResponse)
async def reset_password(
    reset_data: PasswordReset,
    _: bool = Depends(auth_rate_limit)
):
    """
    Reset password using reset token.
    
    - **token**: Password reset token from email
    - **new_password**: New password
    - **confirm_password**: Must match new password
    """
    try:
        success = await auth_service.reset_password(
            reset_data.token, 
            reset_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        logger.info("Password reset completed successfully")
        
        return BaseResponse(
            message="Password reset successfully. Please login with your new password."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed. Please try again."
        )


@router.post("/password/change", response_model=BaseResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user)
):
    """
    Change password for authenticated user.
    
    - **current_password**: Current password
    - **new_password**: New password
    - **confirm_password**: Must match new password
    """
    try:
        success = await auth_service.change_password(
            str(current_user.id),
            password_data.current_password,
            password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        logger.info(f"Password changed for user: {current_user.email}")
        
        return BaseResponse(
            message="Password changed successfully. Please login again."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed. Please try again."
        )


@router.post("/email/verify/request", response_model=BaseResponse)
async def request_email_verification(
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks
):
    """
    Request email verification for current user.
    
    Sends verification email to user's email address.
    """
    try:
        if current_user.email_verified:
            return BaseResponse(message="Email is already verified")
        
        token = await auth_service.create_email_verification_token(str(current_user.id))
        
        # Send verification email in background
        background_tasks.add_task(send_email_verification_email, current_user.email, token)
        
        logger.info(f"Email verification requested for: {current_user.email}")
        
        return BaseResponse(
            message="Verification email sent. Please check your inbox."
        )
        
    except Exception as e:
        logger.error(f"Email verification request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification request failed. Please try again."
        )


@router.post("/email/verify", response_model=BaseResponse)
async def verify_email(verification_data: EmailVerification):
    """
    Verify email address using verification token.
    
    - **token**: Email verification token from email
    """
    try:
        success = await auth_service.verify_email(verification_data.token)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        logger.info("Email verification completed successfully")
        
        return BaseResponse(message="Email verified successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed. Please try again."
        )


# Background tasks for sending emails
async def send_email_verification(user_id: str):
    """Send email verification email (background task)."""
    try:
        # This would integrate with your email service
        # For now, just log the action
        logger.info(f"TODO: Send email verification for user_id: {user_id}")
    except Exception as e:
        logger.error(f"Failed to send email verification: {e}")


async def send_password_reset_email(email: str, token: str):
    """Send password reset email (background task)."""
    try:
        # This would integrate with your email service
        # For now, just log the action
        logger.info(f"TODO: Send password reset email to {email} with token: {token[:10]}...")
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")


async def send_email_verification_email(email: str, token: str):
    """Send email verification email (background task)."""
    try:
        # This would integrate with your email service
        # For now, just log the action
        logger.info(f"TODO: Send email verification to {email} with token: {token[:10]}...")
    except Exception as e:
        logger.error(f"Failed to send email verification email: {e}")
