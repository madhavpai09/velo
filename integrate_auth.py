#!/usr/bin/env python3
"""
Integrate authentication enhancements into server.py
Adds password validation, rate limiting, token management, and OAuth2 support
"""

import re
from pathlib import Path

# Read the current server.py
server_path = Path('serverapp/server.py')
content = server_path.read_text()

# 1. Add new imports after existing imports
new_imports = """from auth.password import PasswordValidator
from auth.rate_limit import RateLimiter
from auth.tokens import TokenManager
from auth.oauth import GoogleOAuthHandler, GitHubOAuthHandler"""

# Find the last import that starts with 'from' and add after it
import_pattern = r'(from utils\.health import HealthCheck)'
replacement = r'\1\n' + new_imports
content = re.sub(import_pattern, replacement, content)

# 2. Update the FastAPI imports to include Request
content = content.replace(
    'from fastapi import FastAPI, Depends, HTTPException, status',
    'from fastapi import FastAPI, Depends, HTTPException, status, Request'
)

# 3. Initialize auth modules after settings initialization
init_pattern = r'(settings = get_settings\(\))(.*?)(\n# NEW: Schemas for School Pool)'
init_replacement = r'''\1

# Initialize authentication modules
password_validator = PasswordValidator()
rate_limiter = RateLimiter(max_attempts=5, window_seconds=900)
token_manager = TokenManager(
    secret_key=settings.secret_key,
    algorithm=settings.algorithm,
    access_token_expire_minutes=settings.access_token_expire_minutes
)
google_oauth = GoogleOAuthHandler()
github_oauth = GitHubOAuthHandler()\2\3'''

content = re.sub(init_pattern, init_replacement, content, flags=re.DOTALL)

# 4. Update Token schema to include refresh_token
token_schema_pattern = r'class Token\(BaseModel\):\n    access_token: str\n    token_type: str'
token_schema_replacement = '''class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str'''

content = content.replace(token_schema_pattern, token_schema_replacement)

# 5. Add new OAuth request schemas before UserCreate
oauth_schemas = '''
class TokenRefreshRequest(BaseModel):
    refresh_token: str

class OAuthCallbackRequest(BaseModel):
    id_token: str
    provider: str = "google"  # "google" or "github"

class OAuthUserInfo(BaseModel):
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    provider: str

'''

# Find where to insert - before class UserCreate
user_create_pos = content.find('class UserCreate(BaseModel):')
content = content[:user_create_pos] + oauth_schemas + content[user_create_pos:]

# 6. Replace signup endpoint
signup_pattern = r'''@app\.post\("/api/signup", response_model=Token\)
def signup\(user: UserCreate, db: Session = Depends\(get_db\)\):
    db_user = db\.query\(User\)\.filter\(User\.email == user\.email\)\.first\(\)
    if db_user:
        raise HTTPException\(status_code=400, detail="Email already registered"\)
    
    hashed_password = get_password_hash\(user\.password\)
    new_user = User\(
        email=user\.email,
        hashed_password=hashed_password,
        full_name=user\.full_name,
        phone_number=user\.phone
    \)
    db\.add\(new_user\)
    db\.commit\(\)
    db\.refresh\(new_user\)
    
    access_token_expires = timedelta\(minutes=ACCESS_TOKEN_EXPIRE_MINUTES\)
    access_token = create_access_token\(
        data=\{"sub": new_user\.email\}, expires_delta=access_token_expires
    \)
    return \{"access_token": access_token, "token_type": "bearer"\}'''

signup_replacement = '''@app.post("/api/signup", response_model=Token)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with enhanced password validation"""
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate password strength
    is_valid, error_msg = password_validator.validate(user.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        phone_number=user.phone,
        auth_provider="local",
        is_email_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create token pair (access + refresh)
    access_token, refresh_token = token_manager.create_token_pair(
        user_id=new_user.id,
        email=new_user.email
    )
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}'''

content = re.sub(signup_pattern, signup_replacement, content, flags=re.DOTALL)

# 7. Replace /api/login endpoint
login_pattern = r'''@app\.post\("/api/login", response_model=Token\)
def login\(form_data: OAuth2PasswordRequestForm = Depends\(\), db: Session = Depends\(get_db\)\):
    # Compatible with OAuth2 standard form
    user = db\.query\(User\)\.filter\(User\.email == form_data\.username\)\.first\(\)
    if not user or not verify_password\(form_data\.password, user\.hashed_password\):
        raise HTTPException\(
            status_code=status\.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers=\{"WWW-Authenticate": "Bearer"\},
        \)
    
    access_token_expires = timedelta\(minutes=ACCESS_TOKEN_EXPIRE_MINUTES\)
    access_token = create_access_token\(
        data=\{"sub": user\.email\}, expires_delta=access_token_expires
    \)
    return \{"access_token": access_token, "token_type": "bearer"\}'''

login_replacement = '''@app.post("/api/login", response_model=Token)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Standard OAuth2 login endpoint with rate limiting and dual-token response"""
    client_ip = request.client.host
    
    # Check rate limiting
    is_allowed, remaining, reset_seconds = rate_limiter.is_allowed(client_ip)
    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Try again in {reset_seconds} seconds",
            headers={"Retry-After": str(reset_seconds)}
        )
    
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create token pair (access + refresh)
    access_token, refresh_token = token_manager.create_token_pair(
        user_id=user.id,
        email=user.email
    )
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}'''

content = re.sub(login_pattern, login_replacement, content, flags=re.DOTALL)

# 8. Replace /api/login/json endpoint
login_json_pattern = r'''@app\.post\("/api/login/json", response_model=Token\)
def login_json\(user_login: UserLogin, db: Session = Depends\(get_db\)\):
    # JSON compatible endpoint for frontend
    user = db\.query\(User\)\.filter\(User\.email == user_login\.email\)\.first\(\)
    if not user or not verify_password\(user_login\.password, user\.hashed_password\):
        raise HTTPException\(
            status_code=status\.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers=\{"WWW-Authenticate": "Bearer"\},
        \)
    
    access_token_expires = timedelta\(minutes=ACCESS_TOKEN_EXPIRE_MINUTES\)
    access_token = create_access_token\(
        data=\{"sub": user\.email\}, expires_delta=access_token_expires
    \)
    return \{"access_token": access_token, "token_type": "bearer"\}'''

login_json_replacement = '''@app.post("/api/login/json", response_model=Token)
def login_json(user_login: UserLogin, request: Request, db: Session = Depends(get_db)):
    """JSON login endpoint with rate limiting and dual-token response"""
    client_ip = request.client.host
    
    # Check rate limiting
    is_allowed, remaining, reset_seconds = rate_limiter.is_allowed(client_ip)
    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Try again in {reset_seconds} seconds",
            headers={"Retry-After": str(reset_seconds)}
        )
    
    user = db.query(User).filter(User.email == user_login.email).first()
    
    # Validate password and auth provider
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create token pair (access + refresh)
    access_token, refresh_token = token_manager.create_token_pair(
        user_id=user.id,
        email=user.email
    )
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}'''

content = re.sub(login_json_pattern, login_json_replacement, content, flags=re.DOTALL)

# 9. Update /api/me endpoint
me_pattern = r'''@app\.get\("/api/me"\)
def read_users_me\(current_user: User = Depends\(get_current_user\)\):
    return \{
        "id": current_user\.id,
        "email": current_user\.email,
        "name": current_user\.full_name,
        "phone": current_user\.phone_number
    \}'''

me_replacement = '''@app.get("/api/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.full_name,
        "phone": current_user.phone_number,
        "auth_provider": getattr(current_user, "auth_provider", "local"),
        "is_email_verified": getattr(current_user, "is_email_verified", False)
    }'''

content = content.replace(me_pattern, me_replacement)

# 10. Add new endpoints after /api/me
new_endpoints = '''

@app.post("/api/auth/refresh", response_model=Token)
def refresh_token_endpoint(req: TokenRefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    try:
        payload = token_manager.validate_refresh_token(req.refresh_token)
        user_id = payload.get("user_id")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create new token pair
        access_token, refresh_token = token_manager.create_token_pair(
            user_id=user.id,
            email=user.email
        )
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.post("/api/auth/google")
async def google_login(req: OAuthCallbackRequest, db: Session = Depends(get_db)):
    """Google OAuth2 login handler"""
    try:
        # Verify Google ID token
        user_info = google_oauth.verify_id_token(req.id_token)
        if not user_info:
            raise HTTPException(status_code=400, detail="Invalid Google token")
        
        # Find or create user
        user = db.query(User).filter(User.email == user_info.email).first()
        if not user:
            # Auto-create user from Google info
            user = User(
                email=user_info.email,
                full_name=user_info.name or user_info.email.split("@")[0],
                auth_provider="google",
                provider_id=user_info.email,
                hashed_password=None,  # OAuth users don't have passwords
                is_email_verified=True  # Google verifies email
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update provider info if needed
            if not user.auth_provider:
                user.auth_provider = "google"
                user.provider_id = user_info.email
                db.commit()
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create token pair
        access_token, refresh_token = token_manager.create_token_pair(
            user_id=user.id,
            email=user.email
        )
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Google login failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Google authentication failed: {str(e)}")

@app.post("/api/auth/github")
async def github_login(req: OAuthCallbackRequest, db: Session = Depends(get_db)):
    """GitHub OAuth2 login handler"""
    try:
        # Verify GitHub access token and get user info
        user_info = github_oauth.get_user_info(req.id_token)  # Note: id_token is actually access_token for GitHub
        if not user_info:
            raise HTTPException(status_code=400, detail="Invalid GitHub token")
        
        # Find or create user
        user = db.query(User).filter(User.email == user_info.email).first()
        if not user:
            # Auto-create user from GitHub info
            user = User(
                email=user_info.email,
                full_name=user_info.name or user_info.email.split("@")[0],
                auth_provider="github",
                provider_id=user_info.email,
                hashed_password=None,  # OAuth users don't have passwords
                is_email_verified=True  # GitHub verifies email
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update provider info if needed
            if not user.auth_provider:
                user.auth_provider = "github"
                user.provider_id = user_info.email
                db.commit()
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create token pair
        access_token, refresh_token = token_manager.create_token_pair(
            user_id=user.id,
            email=user.email
        )
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"GitHub login failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"GitHub authentication failed: {str(e)}")

'''

# Find where to insert - after @app.get("/api/me") and its function
me_endpoint_pos = content.find('@app.get("/api/me")')
me_function_end = content.find('\n@app.post("/driver/register")', me_endpoint_pos)
if me_function_end != -1:
    content = content[:me_function_end] + new_endpoints + content[me_function_end:]

# Write the updated content
server_path.write_text(content)
print("✅ Successfully integrated authentication enhancements into server.py")
print("📊 Changes made:")
print("   - Added new imports for auth modules")
print("   - Initialized password validator, rate limiter, token manager, and OAuth handlers")
print("   - Updated Token schema to include refresh_token")
print("   - Enhanced signup endpoint with password validation")
print("   - Enhanced /api/login with rate limiting and token pair creation")
print("   - Enhanced /api/login/json with rate limiting and token pair creation")
print("   - Updated /api/me to include auth_provider and is_email_verified")
print("   - Added /api/auth/refresh endpoint for token refresh")
print("   - Added /api/auth/google endpoint for Google OAuth2")
print("   - Added /api/auth/github endpoint for GitHub OAuth2")
