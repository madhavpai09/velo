"""
Centralized logging configuration for the application
"""
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
import json
from pythonjsonlogger import jsonlogger
from config import get_settings


def setup_logging():
    """Configure application-wide logging"""
    settings = get_settings()
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.log_level))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level))
    
    # JSON formatter for structured logging
    json_formatter = jsonlogger.JsonFormatter(
        fmt='%(timestamp)s %(level)s %(name)s %(message)s %(filename)s %(funcName)s %(lineno)d',
        timestamp=True
    )
    
    console_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)
    
    # File handler for production (only if not in development)
    if settings.environment != "development":
        file_handler = RotatingFileHandler(
            f"logs/mini_uber_{datetime.now().strftime('%Y-%m-%d')}.log",
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(getattr(logging, settings.log_level))
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)
    
    # Log startup info
    logger.info(f"Logging initialized", extra={
        "environment": settings.environment,
        "log_level": settings.log_level
    })
    
    return logger


# Request logging middleware logger
request_logger = logging.getLogger("request")

def log_request(method: str, path: str, status_code: int, duration_ms: float, user_id: int = None):
    """Log API request with timing"""
    request_logger.info(
        "API Request",
        extra={
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "user_id": user_id
        }
    )
