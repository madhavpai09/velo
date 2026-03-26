"""
Enhanced token management with refresh tokens
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from jose import jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session
from config import get_settings
import secrets


settings = get_settings()


class Token(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenPayload(BaseModel):
    """Refresh token request"""
    refresh_token: str


class TokenManager:
    """Manage access and refresh tokens"""
    
    ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Short-lived access tokens
    REFRESH_TOKEN_EXPIRE_DAYS = 7  # Longer-lived refresh tokens
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a short-lived access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=TokenManager.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(user_id: int) -> str:
        """Create a long-lived refresh token"""
        expire = datetime.now(timezone.utc) + timedelta(days=TokenManager.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
            "jti": secrets.token_urlsafe(32)  # Unique token identifier
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )
        return encoded_jwt
    
    @staticmethod
    def create_token_pair(user_id: int, email: str = None) -> Token:
        """
        Create both access and refresh tokens
        
        Returns:
            Token: Contains access_token, refresh_token, and expiration info
        """
        access_token = TokenManager.create_access_token({"sub": email or str(user_id)})
        refresh_token = TokenManager.create_refresh_token(user_id)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=TokenManager.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """
        Decode and validate token
        
        Returns:
            dict: Token payload if valid
            None: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm]
            )
            return payload
        except Exception as e:
            print(f"Token decode error: {e}")
            return None
    
    @staticmethod
    def is_token_expired(token_payload: dict) -> bool:
        """Check if token is expired"""
        if not token_payload or "exp" not in token_payload:
            return True
        
        exp_timestamp = token_payload["exp"]
        return datetime.fromtimestamp(exp_timestamp, tz=timezone.utc) < datetime.now(timezone.utc)
    
    @staticmethod
    def get_token_type(token_payload: dict) -> str:
        """Get token type (access or refresh)"""
        return token_payload.get("type", "unknown") if token_payload else None
    
    @staticmethod
    def validate_access_token(token: str) -> Tuple[bool, Optional[dict]]:
        """Validate access token"""
        payload = TokenManager.decode_token(token)
        
        if not payload:
            return False, None
        
        if TokenManager.is_token_expired(payload):
            return False, None
        
        if TokenManager.get_token_type(payload) != "access":
            return False, None
        
        return True, payload
    
    @staticmethod
    def validate_refresh_token(token: str) -> Tuple[bool, Optional[dict]]:
        """Validate refresh token"""
        payload = TokenManager.decode_token(token)
        
        if not payload:
            return False, None
        
        if TokenManager.is_token_expired(payload):
            return False, None
        
        if TokenManager.get_token_type(payload) != "refresh":
            return False, None
        
        return True, payload
