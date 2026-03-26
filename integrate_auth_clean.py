#!/usr/bin/env python3
"""
Clean integration of authentication enhancements into server.py
This script carefully updates the file line by line
"""

import sys
from pathlib import Path

def update_server_py():
    server_path = Path('serverapp/server.py')
    
    # Read current content
    with open(server_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Step 1: Fix imports - add Request to FastAPI imports and auth module imports
    for i, line in enumerate(lines):
        if 'from fastapi import FastAPI, Depends, HTTPException, status' in line:
            if 'Request' not in line:
                lines[i] = 'from fastapi import FastAPI, Depends, HTTPException, status, Request\n'
        
        if 'from utils.health import HealthCheck' in line:
            # Insert auth imports after this line
            if 'from auth.password' not in ''.join(lines):
                auth_imports = '''from auth.password import PasswordValidator
from auth.rate_limit import RateLimiter
from auth.tokens import TokenManager
from auth.oauth import GoogleOAuthHandler, GitHubOAuthHandler
'''
                lines.insert(i + 1, auth_imports)
            break
    
    # Step 2: Add auth module initialization after settings = get_settings()
    for i, line in enumerate(lines):
        if 'settings = get_settings()' in line:
            # Check if auth initialization already exists
            if 'password_validator = PasswordValidator()' not in ''.join(lines[i:i+10]):
                auth_init = '''
# Initialize authentication modules
password_validator = PasswordValidator()
rate_limiter = RateLimiter(max_attempts=5, window_seconds=900)
token_manager = TokenManager(
    secret_key=settings.secret_key,
    algorithm=settings.algorithm,
    access_token_expire_minutes=settings.access_token_expire_minutes
)
google_oauth = GoogleOAuthHandler()
github_oauth = GitHubOAuthHandler()
'''
                lines.insert(i + 1, auth_init)
            break
    
    # Step 3: Update Token schema
    for i, line in enumerate(lines):
        if 'class Token(BaseModel):' in line:
            # Find the class definition and update it
            j = i
            while j < len(lines) and 'access_token: str' in lines[j+1]:
                j += 1
            # Find the token_type line
            for k in range(i, min(i+10, len(lines))):
                if 'token_type: str' in lines[k]:
                    # Insert refresh_token before token_type
                    if 'refresh_token' not in ''.join(lines[i:k+1]):
                        lines.insert(k, '    refresh_token: Optional[str] = None\n')
                    break
            break
    
    # Step 4: Add new schemas before UserCreate
    for i, line in enumerate(lines):
        if 'class UserCreate(BaseModel):' in line:
            if 'TokenRefreshRequest' not in ''.join(lines[max(0, i-20):i]):
                new_schemas = '''
class TokenRefreshRequest(BaseModel):
    refresh_token: str

class OAuthCallbackRequest(BaseModel):
    id_token: str
    provider: str = "google"

class OAuthUserInfo(BaseModel):
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    provider: str

'''
                lines.insert(i, new_schemas)
            break
    
    # Write updated content
    with open(server_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Successfully updated server.py with authentication enhancements!")
    print("   - Added Request import")
    print("   - Added auth module imports")
    print("   - Initialized auth modules")
    print("   - Updated Token schema with refresh_token")
    print("   - Added OAuth request/response schemas")
    print("\n⚠️  Manual steps still needed:")
    print("   1. Update /api/signup endpoint")
    print("   2. Update /api/login endpoint")
    print("   3. Update /api/login/json endpoint")
    print("   4. Add /api/auth/refresh endpoint")
    print("   5. Add /api/auth/google endpoint")
    print("   6. Add /api/auth/github endpoint")
    print("\n   See AUTH_IMPLEMENTATION_GUIDE.md for exact code")

if __name__ == '__main__':
    try:
        update_server_py()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
