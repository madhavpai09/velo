"""
OAuth2 handlers for social login (Google, GitHub, etc.)
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel
import httpx
import logging

logger = logging.getLogger(__name__)


class OAuthToken(BaseModel):
    """OAuth token from provider"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class OAuthUserInfo(BaseModel):
    """User information from OAuth provider"""
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    verified_email: bool = False


class GoogleOAuthHandler:
    """Handle Google OAuth2 authentication"""
    
    GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/tokeninfo"
    GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    @staticmethod
    async def verify_id_token(id_token: str, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Verify Google ID token from frontend
        
        Args:
            id_token: ID token from Google (from frontend)
            client_id: Your Google Client ID
        
        Returns:
            User info dict if valid, None if invalid
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    GoogleOAuthHandler.GOOGLE_TOKEN_ENDPOINT,
                    params={"id_token": id_token}
                )
                
                if response.status_code != 200:
                    logger.error(f"Google token verification failed: {response.text}")
                    return None
                
                data = response.json()
                
                # Verify audience (client_id)
                if data.get("aud") != client_id:
                    logger.error(f"Invalid audience: {data.get('aud')} != {client_id}")
                    return None
                
                return {
                    "id": data.get("sub"),
                    "email": data.get("email"),
                    "name": data.get("name"),
                    "picture": data.get("picture"),
                    "email_verified": data.get("email_verified", False)
                }
        
        except Exception as e:
            logger.error(f"Google token verification error: {e}")
            return None
    
    @staticmethod
    async def get_user_info(access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from Google using access token
        
        Args:
            access_token: Google access token
        
        Returns:
            User info dict if successful
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    GoogleOAuthHandler.GOOGLE_USERINFO_ENDPOINT,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Google userinfo failed: {response.text}")
                    return None
                
                data = response.json()
                
                return {
                    "id": data.get("id"),
                    "email": data.get("email"),
                    "name": data.get("name"),
                    "picture": data.get("picture"),
                    "email_verified": data.get("verified_email", False)
                }
        
        except Exception as e:
            logger.error(f"Google userinfo error: {e}")
            return None


class GitHubOAuthHandler:
    """Handle GitHub OAuth2 authentication"""
    
    GITHUB_USERINFO_ENDPOINT = "https://api.github.com/user"
    GITHUB_USER_EMAIL_ENDPOINT = "https://api.github.com/user/emails"
    
    @staticmethod
    async def get_user_info(access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from GitHub using access token
        
        Args:
            access_token: GitHub access token
        
        Returns:
            User info dict if successful
        """
        try:
            async with httpx.AsyncClient() as client:
                # Get user info
                response = await client.get(
                    GitHubOAuthHandler.GITHUB_USERINFO_ENDPOINT,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"GitHub userinfo failed: {response.text}")
                    return None
                
                user_data = response.json()
                
                # Get user emails
                email_response = await client.get(
                    GitHubOAuthHandler.GITHUB_USER_EMAIL_ENDPOINT,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                
                emails = email_response.json() if email_response.status_code == 200 else []
                primary_email = next((e["email"] for e in emails if e.get("primary")), user_data.get("email"))
                
                return {
                    "id": user_data.get("id"),
                    "email": primary_email,
                    "name": user_data.get("name") or user_data.get("login"),
                    "picture": user_data.get("avatar_url"),
                    "email_verified": True  # GitHub verifies emails
                }
        
        except Exception as e:
            logger.error(f"GitHub userinfo error: {e}")
            return None


# Request schema for OAuth sign in
class GoogleSignInRequest(BaseModel):
    """Google Sign-In request from frontend"""
    id_token: str  # ID token from Google (frontend)
    access_token: Optional[str] = None  # Optional access token


class GitHubSignInRequest(BaseModel):
    """GitHub Sign-In request"""
    code: str  # Authorization code from GitHub
    state: str  # State for CSRF protection
