"""
Logging configuration for PromoWeb Africa API.
Provides structured logging with rotation and different outputs.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

from app.core.config import get_settings

settings = get_settings()


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "ip_address"):
            log_data["ip_address"] = record.ip_address
        
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint
        
        if hasattr(record, "method"):
            log_data["method"] = record.method
        
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        
        if hasattr(record, "response_time"):
            log_data["response_time"] = record.response_time
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    # Color codes
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{level_color}{record.levelname}{self.RESET}"
        
        # Format message
        formatted = super().format(record)
        
        return formatted


def setup_logging() -> None:
    """Setup logging configuration."""
    
    # Create logs directory
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    if settings.DEBUG:
        console_format = (
            "%(asctime)s | %(levelname)-8s | %(name)-20s | "
            "%(funcName)-15s:%(lineno)-3d | %(message)s"
        )
        console_formatter = ColoredFormatter(console_format)
    else:
        console_formatter = JSONFormatter()
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_SIZE,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_log_file = log_dir / "error.log"
    error_handler = logging.handlers.RotatingFileHandler(
        filename=error_log_file,
        maxBytes=settings.LOG_MAX_SIZE,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(error_handler)
    
    # Set third-party library log levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("aioredis").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class RequestLogger:
    """Logger for HTTP requests with additional context."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        response_time: float,
        user_id: str = None,
        ip_address: str = None,
        request_id: str = None,
        **kwargs
    ) -> None:
        """
        Log HTTP request with context.
        
        Args:
            method: HTTP method
            endpoint: Request endpoint
            status_code: Response status code
            response_time: Response time in seconds
            user_id: User ID if authenticated
            ip_address: Client IP address
            request_id: Request ID for tracing
            **kwargs: Additional context
        """
        level = logging.INFO
        if status_code >= 500:
            level = logging.ERROR
        elif status_code >= 400:
            level = logging.WARNING
        
        message = f"{method} {endpoint} - {status_code} - {response_time:.3f}s"
        
        # Create log record with extra fields
        extra = {
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "response_time": response_time,
        }
        
        if user_id:
            extra["user_id"] = user_id
        if ip_address:
            extra["ip_address"] = ip_address
        if request_id:
            extra["request_id"] = request_id
        
        extra.update(kwargs)
        
        self.logger.log(level, message, extra=extra)
    
    def log_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        user_id: str = None,
        request_id: str = None,
    ) -> None:
        """
        Log error with context.
        
        Args:
            error: Exception instance
            context: Additional context
            user_id: User ID if available
            request_id: Request ID for tracing
        """
        extra = {}
        if user_id:
            extra["user_id"] = user_id
        if request_id:
            extra["request_id"] = request_id
        if context:
            extra.update(context)
        
        self.logger.error(
            f"Error: {str(error)}",
            exc_info=True,
            extra=extra
        )


# Global request logger
request_logger = RequestLogger(get_logger("promoweb.requests"))
