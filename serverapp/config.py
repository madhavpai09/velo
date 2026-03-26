"""
Configuration management for different environments (dev, staging, prod)
Uses environment variables with sensible defaults
"""
import os
from typing import List, Optional
from pydantic import BaseModel
from functools import lru_cache


class Settings(BaseModel):
    """Main application settings"""
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # Database
    database_url: str = "postgresql://Mini_Uber_user:password@localhost:5432/Mini_Uber"
    
    # API
    api_title: str = "Mini Uber API"
    api_version: str = "1.0.0"
    api_description: str = "Ride-hailing platform with School Pool Pass feature"
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200
    refresh_token_expire_days: int = 7
    
    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Logging
    log_level: str = "INFO"
    
    # Rate Limiting
    enable_rate_limiting: bool = True
    rate_limit_requests: int = 100
    rate_limit_period: int = 60
    
    # Feature Flags
    enable_school_pool: bool = True
    
    # External Services
    osrm_api_url: str = "http://router.project-osrm.org"
    maps_api_key: Optional[str] = None
    
    # Error Tracking
    sentry_dsn: Optional[str] = None
    
    # Email Configuration
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    sender_email: Optional[str] = None
    
    # OAuth
    google_client_id: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings from environment variables
    Uses sensible defaults for development
    """
    return Settings(
        environment=os.getenv("ENVIRONMENT", "development"),
        debug=os.getenv("ENVIRONMENT", "development") == "development",
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql://Mini_Uber_user:password@localhost:5432/Mini_Uber"
        ),
        secret_key=os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"),
        algorithm=os.getenv("ALGORITHM", "HS256"),
        access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200")),
        refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        enable_rate_limiting=os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true",
        rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
        rate_limit_period=int(os.getenv("RATE_LIMIT_PERIOD", "60")),
        enable_school_pool=os.getenv("ENABLE_SCHOOL_POOL", "true").lower() == "true",
        osrm_api_url=os.getenv("OSRM_API_URL", "http://router.project-osrm.org"),
        maps_api_key=os.getenv("MAPS_API_KEY"),
        sentry_dsn=os.getenv("SENTRY_DSN"),
        smtp_server=os.getenv("SMTP_SERVER"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_user=os.getenv("SMTP_USER"),
        smtp_password=os.getenv("SMTP_PASSWORD"),
        sender_email=os.getenv("SENDER_EMAIL"),
        google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
        github_client_id=os.getenv("GITHUB_CLIENT_ID", ""),
        github_client_secret=os.getenv("GITHUB_CLIENT_SECRET", ""),
    )


# Validate security settings in production
def validate_production_settings(settings: Settings) -> None:
    """Validate that critical settings are properly configured for production"""
    if settings.environment == "production":
        errors = []
        
        if settings.secret_key == "dev-secret-key-change-in-production":
            errors.append("❌ SECRET_KEY must be changed from default in production")
        
        if "localhost" in settings.database_url or "127.0.0.1" in settings.database_url:
            errors.append("❌ DATABASE_URL should not point to localhost in production")
        
        if not settings.sentry_dsn:
            errors.append("⚠️  SENTRY_DSN not configured - error tracking disabled")
        
        if errors:
            for error in errors:
                print(error)
            if any("❌" in e for e in errors):
                raise ValueError("Production configuration is incomplete. Please set required environment variables.")
