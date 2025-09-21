"""
Custom middleware for PromoWeb Africa API.
Includes security, rate limiting, and request tracking.
"""

import time
import uuid
from typing import Callable, Dict, Any
import logging

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.redis import get_cache
from app.core.logging import request_logger

logger = logging.getLogger(__name__)


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    """Middleware to add process time header and log requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Get client IP
        client_ip = request.client.host
        if forwarded_for := request.headers.get("X-Forwarded-For"):
            client_ip = forwarded_for.split(",")[0].strip()
        elif real_ip := request.headers.get("X-Real-IP"):
            client_ip = real_ip
        
        request.state.client_ip = client_ip
        
        # Start timing
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate process time
        process_time = time.time() - start_time
        
        # Add headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        # Log request
        request_logger.log_request(
            method=request.method,
            endpoint=str(request.url.path),
            status_code=response.status_code,
            response_time=process_time,
            ip_address=client_ip,
            request_id=request_id,
            user_agent=request.headers.get("User-Agent"),
            query_params=str(request.query_params) if request.query_params else None,
        )
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""
    
    def __init__(
        self,
        app: ASGIApp,
        calls: int = 100,
        period: int = 60,
        exempt_paths: list = None,
    ):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.exempt_paths = exempt_paths or []
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Skip for health checks and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client identifier
        client_ip = getattr(request.state, "client_ip", request.client.host)
        
        # Create rate limit key
        rate_limit_key = f"rate_limit:{client_ip}"
        
        try:
            cache = get_cache()
            
            # Get current count
            current_calls = await cache.get(rate_limit_key)
            if current_calls is None:
                current_calls = 0
            else:
                current_calls = int(current_calls)
            
            # Check if limit exceeded
            if current_calls >= self.calls:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": self.period,
                    },
                    headers={
                        "Retry-After": str(self.period),
                        "X-RateLimit-Limit": str(self.calls),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + self.period),
                    }
                )
            
            # Increment counter
            await cache.incr(rate_limit_key)
            
            # Set expiration on first call
            if current_calls == 0:
                await cache.expire(rate_limit_key, self.period)
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            remaining = max(0, self.calls - current_calls - 1)
            response.headers["X-RateLimit-Limit"] = str(self.calls)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.period)
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Continue without rate limiting if Redis fails
            return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), "
            "gyroscope=(), magnetometer=(), microphone=(), "
            "payment=(), usb=()"
        )
        
        # Add CSP header for non-API routes
        if not request.url.path.startswith("/api/"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none';"
            )
        
        return response


class CORSPreflightMiddleware(BaseHTTPMiddleware):
    """Custom CORS preflight handling."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method == "OPTIONS":
            # Handle preflight requests
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-Requested-With, Accept"
            )
            response.headers["Access-Control-Max-Age"] = "86400"
            return response
        
        return await call_next(request)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        
        except HTTPException:
            # Re-raise HTTP exceptions (handled by FastAPI)
            raise
        
        except Exception as e:
            # Log unexpected errors
            request_logger.log_error(
                error=e,
                context={
                    "method": request.method,
                    "url": str(request.url),
                    "headers": dict(request.headers),
                },
                request_id=getattr(request.state, "request_id", None),
            )
            
            # Return generic error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal server error",
                    "request_id": getattr(request.state, "request_id", None),
                }
            )


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request body size."""
    
    def __init__(self, app: ASGIApp, max_size: int = 10 * 1024 * 1024):  # 10MB
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check content length header
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "detail": f"Request body too large. Maximum size: {self.max_size} bytes"
                }
            )
        
        return await call_next(request)


class DatabaseTransactionMiddleware(BaseHTTPMiddleware):
    """Middleware to handle database transactions for write operations."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only handle write operations
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            # The actual transaction handling is done in the endpoint dependencies
            # This middleware just adds transaction context to the request
            request.state.requires_transaction = True
        
        return await call_next(request)
