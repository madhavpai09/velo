"""
Rate limiting decorator for protecting authentication endpoints
"""
from functools import wraps
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import Callable, Dict, Tuple
import time


class RateLimiter:
    """
    Simple in-memory rate limiter
    For production, use Redis-based rate limiter
    """
    
    def __init__(self):
        self.attempts: Dict[str, list[float]] = defaultdict(list)
    
    def is_allowed(self, key: str, max_attempts: int = 5, window_seconds: int = 900) -> Tuple[bool, int, int]:
        """
        Check if action is allowed
        Returns: (is_allowed, remaining_attempts, reset_seconds)
        """
        now = time.time()
        cutoff = now - window_seconds
        
        # Remove old attempts
        self.attempts[key] = [t for t in self.attempts[key] if t > cutoff]
        
        # Check if allowed
        remaining = max_attempts - len(self.attempts[key])
        reset_seconds = int(self.attempts[key][0] - cutoff) + 1 if self.attempts[key] else 0
        
        is_allowed = len(self.attempts[key]) < max_attempts
        
        if not is_allowed:
            # Record this attempt
            self.attempts[key].append(now)
        else:
            # Record this attempt
            self.attempts[key].append(now)
        
        return is_allowed, max(0, remaining - 1), max(0, reset_seconds)
    
    def reset(self, key: str):
        """Reset attempts for a key"""
        if key in self.attempts:
            del self.attempts[key]


# Global rate limiter instance
_limiter = RateLimiter()


def rate_limit(max_attempts: int = 5, window_seconds: int = 900, key_func: Callable = None):
    """
    Decorator for rate limiting
    
    Args:
        max_attempts: Maximum attempts allowed
        window_seconds: Time window in seconds (default 15 minutes)
        key_func: Function to extract rate limit key from request (default: IP address)
    
    Usage:
        @app.post("/login")
        @rate_limit(max_attempts=5, window_seconds=900)
        def login(request: Request, ...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, request=None, **kwargs):
            # Extract rate limit key
            if key_func:
                key = key_func(request)
            else:
                # Default: use IP address
                client_ip = request.client.host if request and hasattr(request, 'client') else "unknown"
                endpoint = request.url.path if request else "unknown"
                key = f"{endpoint}:{client_ip}"
            
            # Check rate limit
            is_allowed, remaining, reset_seconds = _limiter.is_allowed(key, max_attempts, window_seconds)
            
            if not is_allowed:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many attempts. Try again in {reset_seconds} seconds.",
                    headers={"Retry-After": str(reset_seconds)}
                )
            
            # Add rate limit info to response
            response = await func(*args, request=request, **kwargs)
            
            # If response is a dict, add rate limit headers
            if isinstance(response, dict):
                response["_rate_limit_remaining"] = remaining
            
            return response
        
        @wraps(func)
        def sync_wrapper(*args, request=None, **kwargs):
            # Extract rate limit key
            if key_func:
                key = key_func(request)
            else:
                # Default: use IP address
                client_ip = request.client.host if request and hasattr(request, 'client') else "unknown"
                endpoint = request.url.path if request else "unknown"
                key = f"{endpoint}:{client_ip}"
            
            # Check rate limit
            is_allowed, remaining, reset_seconds = _limiter.is_allowed(key, max_attempts, window_seconds)
            
            if not is_allowed:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many attempts. Try again in {reset_seconds} seconds.",
                    headers={"Retry-After": str(reset_seconds)}
                )
            
            # Call function
            response = func(*args, request=request, **kwargs)
            
            # If response is a dict, add rate limit headers
            if isinstance(response, dict):
                response["_rate_limit_remaining"] = remaining
            
            return response
        
        # Return appropriate wrapper
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Get limiter instance for manual checks
def get_rate_limiter() -> RateLimiter:
    """Get the rate limiter instance"""
    return _limiter
