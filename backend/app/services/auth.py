"""
Authentication service for PromoWeb Africa.
Handles JWT token generation, validation, and user authentication.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.database import get_db_context
from app.core.redis import get_cache
from app.models.user import User, UserSession, UserPasswordReset, UserEmailVerification
from app.schemas.user import UserCreate, UserLogin, TokenData
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service for user management and JWT tokens."""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_EXPIRATION_TIME // 60
        self.refresh_token_expire_days = settings.JWT_REFRESH_EXPIRATION_TIME // (24 * 3600)
        self.cache = get_cache()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[TokenData]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                return None
            
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            role: str = payload.get("role")
            
            if user_id is None:
                return None
            
            return TokenData(user_id=user_id, email=email, role=role)
        except JWTError:
            return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        async with get_db_context() as db:
            # Get user with preferences
            stmt = select(User).where(
                User.email == email,
                User.is_active == True
            ).options(selectinload(User.addresses))
            
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            if not self.verify_password(password, user.password_hash):
                return None
            
            # Update last login
            await db.execute(
                update(User)
                .where(User.id == user.id)
                .values(last_login=datetime.utcnow())
            )
            await db.commit()
            
            return user
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        async with get_db_context() as db:
            # Check if user exists
            existing_user = await db.execute(
                select(User).where(User.email == user_data.email)
            )
            if existing_user.scalar_one_or_none():
                raise ValueError("User with this email already exists")
            
            # Create user
            hashed_password = self.get_password_hash(user_data.password)
            user = User(
                email=user_data.email,
                password_hash=hashed_password,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                phone=user_data.phone,
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"Created new user: {user.email}")
            return user
    
    async def create_user_session(
        self, 
        user: User, 
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[str, str]:
        """Create user session and return access/refresh tokens."""
        # Generate tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)
        
        # Create session record
        async with get_db_context() as db:
            session = UserSession(
                user_id=user.id,
                session_token=access_token[:50],  # Store partial token for identification
                refresh_token=refresh_token,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes),
            )
            
            db.add(session)
            await db.commit()
        
        # Cache user session
        await self.cache.set(
            f"user_session:{user.id}",
            {
                "user_id": str(user.id),
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
            },
            ttl=self.access_token_expire_minutes * 60
        )
        
        return access_token, refresh_token
    
    async def refresh_token(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """Refresh access token using refresh token."""
        token_data = self.verify_token(refresh_token, "refresh")
        if not token_data:
            return None
        
        async with get_db_context() as db:
            # Verify session exists and is active
            session = await db.execute(
                select(UserSession)
                .where(
                    UserSession.refresh_token == refresh_token,
                    UserSession.is_active == True
                )
                .options(selectinload(UserSession.user))
            )
            session = session.scalar_one_or_none()
            
            if not session or not session.user.is_active:
                return None
            
            # Generate new tokens
            new_token_data = {
                "sub": str(session.user.id),
                "email": session.user.email,
                "role": session.user.role,
            }
            
            new_access_token = self.create_access_token(new_token_data)
            new_refresh_token = self.create_refresh_token(new_token_data)
            
            # Update session
            session.session_token = new_access_token[:50]
            session.refresh_token = new_refresh_token
            session.expires_at = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            session.last_activity = datetime.utcnow()
            
            await db.commit()
            
            # Update cache
            await self.cache.set(
                f"user_session:{session.user.id}",
                {
                    "user_id": str(session.user.id),
                    "email": session.user.email,
                    "role": session.user.role,
                    "is_active": session.user.is_active,
                },
                ttl=self.access_token_expire_minutes * 60
            )
            
            return new_access_token, new_refresh_token
    
    async def revoke_session(self, user_id: str, session_token: str) -> bool:
        """Revoke a user session."""
        async with get_db_context() as db:
            result = await db.execute(
                update(UserSession)
                .where(
                    UserSession.user_id == user_id,
                    UserSession.session_token.startswith = session_token[:50],
                    UserSession.is_active == True
                )
                .values(is_active=False)
            )
            await db.commit()
            
            # Remove from cache
            await self.cache.delete(f"user_session:{user_id}")
            
            return result.rowcount > 0
    
    async def revoke_all_sessions(self, user_id: str) -> int:
        """Revoke all user sessions."""
        async with get_db_context() as db:
            result = await db.execute(
                update(UserSession)
                .where(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
                .values(is_active=False)
            )
            await db.commit()
            
            # Remove from cache
            await self.cache.delete(f"user_session:{user_id}")
            
            return result.rowcount
    
    async def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from token."""
        token_data = self.verify_token(token)
        if not token_data:
            return None
        
        # Try cache first
        cached_user = await self.cache.get(f"user_session:{token_data.user_id}")
        if cached_user and cached_user.get("is_active"):
            # Get full user from database
            async with get_db_context() as db:
                user = await db.execute(
                    select(User)
                    .where(User.id == token_data.user_id)
                    .options(selectinload(User.addresses))
                )
                return user.scalar_one_or_none()
        
        return None
    
    async def create_password_reset_token(self, email: str) -> Optional[str]:
        """Create password reset token."""
        async with get_db_context() as db:
            user = await db.execute(
                select(User).where(User.email == email, User.is_active == True)
            )
            user = user.scalar_one_or_none()
            
            if not user:
                return None
            
            # Generate secure token
            token = secrets.token_urlsafe(32)
            
            # Create reset record
            reset = UserPasswordReset(
                user_id=user.id,
                token=token,
                expires_at=datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
            )
            
            db.add(reset)
            await db.commit()
            
            logger.info(f"Created password reset token for user: {email}")
            return token
    
    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using token."""
        async with get_db_context() as db:
            # Get reset token
            reset = await db.execute(
                select(UserPasswordReset)
                .where(
                    UserPasswordReset.token == token,
                    UserPasswordReset.is_used == False,
                    UserPasswordReset.expires_at > datetime.utcnow()
                )
                .options(selectinload(UserPasswordReset.user))
            )
            reset = reset.scalar_one_or_none()
            
            if not reset:
                return False
            
            # Update password
            reset.user.password_hash = self.get_password_hash(new_password)
            reset.is_used = True
            reset.used_at = datetime.utcnow()
            
            # Revoke all sessions
            await db.execute(
                update(UserSession)
                .where(UserSession.user_id == reset.user.id)
                .values(is_active=False)
            )
            
            await db.commit()
            
            # Clear cache
            await self.cache.delete(f"user_session:{reset.user.id}")
            
            logger.info(f"Password reset successful for user: {reset.user.email}")
            return True
    
    async def create_email_verification_token(self, user_id: str) -> str:
        """Create email verification token."""
        async with get_db_context() as db:
            # Generate secure token
            token = secrets.token_urlsafe(32)
            
            user = await db.get(User, user_id)
            if not user:
                raise ValueError("User not found")
            
            # Create verification record
            verification = UserEmailVerification(
                user_id=user_id,
                token=token,
                email=user.email,
                expires_at=datetime.utcnow() + timedelta(days=1)  # 24 hour expiry
            )
            
            db.add(verification)
            await db.commit()
            
            return token
    
    async def verify_email(self, token: str) -> bool:
        """Verify email using token."""
        async with get_db_context() as db:
            # Get verification token
            verification = await db.execute(
                select(UserEmailVerification)
                .where(
                    UserEmailVerification.token == token,
                    UserEmailVerification.is_used == False,
                    UserEmailVerification.expires_at > datetime.utcnow()
                )
                .options(selectinload(UserEmailVerification.user))
            )
            verification = verification.scalar_one_or_none()
            
            if not verification:
                return False
            
            # Update user verification status
            verification.user.email_verified = True
            verification.is_used = True
            verification.verified_at = datetime.utcnow()
            
            await db.commit()
            
            logger.info(f"Email verified for user: {verification.user.email}")
            return True
    
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change user password."""
        async with get_db_context() as db:
            user = await db.get(User, user_id)
            if not user:
                return False
            
            # Verify current password
            if not self.verify_password(current_password, user.password_hash):
                return False
            
            # Update password
            user.password_hash = self.get_password_hash(new_password)
            await db.commit()
            
            # Revoke all other sessions
            await self.revoke_all_sessions(user_id)
            
            logger.info(f"Password changed for user: {user.email}")
            return True


# Global auth service instance
auth_service = AuthService()
