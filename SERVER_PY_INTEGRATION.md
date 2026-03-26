# Server.py Integration Guide

This file shows exactly what needs to be added to `serverapp/server.py` to enable all the new authentication features.

---

## 1. ADD IMPORTS AT THE TOP

```python
# Add these imports to the existing imports in server.py

from fastapi import Request
from datetime import datetime
from auth import (
    TokenManager,
    PasswordValidator,
    rate_limit,
    GoogleOAuthHandler
)
from auth.oauth import GoogleSignInRequest
import logging

# Setup logging
logger = logging.getLogger(__name__)
```

---

## 2. REPLACE THE EXISTING SIGNUP ENDPOINT

### FIND THIS:
```python
@app.post("/api/signup", response_model=Token)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        phone_number=user.phone
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
```

### REPLACE WITH THIS:
```python
@app.post("/api/signup", response_model=dict)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create new user account with password validation and token pair
    """
    # ✅ NEW: Validate password strength
    is_valid, error_msg = PasswordValidator.validate(user.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Check if email already registered
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        logger.warning(f"Signup attempted with existing email: {user.email}")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = get_password_hash(user.password)
    
    # Create user with OAuth fields
    new_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        phone_number=user.phone,
        auth_provider="local",  # ✅ NEW
        is_email_verified=False,  # ✅ NEW
        created_at=datetime.utcnow()  # ✅ NEW
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # ✅ NEW: Use TokenManager to create token pair
    token_pair = TokenManager.create_token_pair(user_id=new_user.id, email=new_user.email)
    
    logger.info(f"New user registered: {new_user.email}")
    
    return {
        "access_token": token_pair.access_token,
        "refresh_token": token_pair.refresh_token,
        "token_type": "bearer",
        "expires_in": token_pair.expires_in,
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.full_name
        }
    }
```

---

## 3. REPLACE THE EXISTING LOGIN ENDPOINT

### FIND THIS:
```python
@app.post("/api/login/json", response_model=Token)
def login_json(user_login: UserLogin, db: Session = Depends(get_db)):
    # JSON compatible endpoint for frontend
    user = db.query(User).filter(User.email == user_login.email).first()
    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
```

### REPLACE WITH THIS:
```python
@app.post("/api/login/json")
@rate_limit(max_attempts=5, window_seconds=900)  # ✅ NEW: Rate limited to 5 attempts per 15 min
async def login_json(request: Request, user_login: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password - RATE LIMITED
    Returns access and refresh tokens
    """
    client_ip = request.client.host
    
    # Find user
    user = db.query(User).filter(User.email == user_login.email).first()
    
    # Verify credentials
    if not user or not verify_password(user_login.password, user.hashed_password):
        logger.warning(f"Failed login attempt for {user_login.email} from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # ✅ NEW: Update last login timestamp
    user.last_login = datetime.utcnow()
    db.commit()
    
    # ✅ NEW: Use TokenManager to create token pair
    token_pair = TokenManager.create_token_pair(user_id=user.id, email=user.email)
    
    logger.info(f"User {user.email} logged in from {client_ip}")
    
    return {
        "access_token": token_pair.access_token,
        "refresh_token": token_pair.refresh_token,
        "token_type": "bearer",
        "expires_in": token_pair.expires_in
    }
```

---

## 4. ADD NEW ENDPOINTS

Add these NEW endpoints after your existing auth endpoints:

```python
# ============================================
# ✅ NEW: Token Refresh Endpoint
# ============================================
@app.post("/api/auth/refresh")
def refresh_access_token(request: dict, db: Session = Depends(get_db)):
    """
    Refresh an expired access token using a refresh token
    
    Request body:
    {
        "refresh_token": "eyJ..."
    }
    
    Returns new access token valid for 15 more minutes
    """
    refresh_token = request.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required"
        )
    
    # ✅ Validate refresh token
    is_valid, payload = TokenManager.validate_refresh_token(refresh_token)
    
    if not is_valid:
        logger.warning("Invalid refresh token attempted")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Get user
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # ✅ Create new token pair
    token_pair = TokenManager.create_token_pair(user_id=user.id, email=user.email)
    
    logger.info(f"Token refreshed for user {user.id}")
    
    return {
        "access_token": token_pair.access_token,
        "refresh_token": token_pair.refresh_token,
        "token_type": "bearer",
        "expires_in": token_pair.expires_in
    }


# ============================================
# ✅ NEW: Google Sign-In Endpoint
# ============================================
@app.post("/api/auth/google")
async def google_signin(google_request: GoogleSignInRequest, db: Session = Depends(get_db)):
    """
    Authenticate with Google using ID token from frontend
    
    Request body:
    {
        "id_token": "eyJ..."  # ID token from Google
    }
    
    Returns:
    {
        "access_token": "...",
        "refresh_token": "...",
        "user": { "id", "email", "name" }
    }
    """
    # ✅ Verify Google ID token
    user_info = await GoogleOAuthHandler.verify_id_token(
        id_token=google_request.id_token,
        client_id=settings.google_client_id  # Set this in .env
    )
    
    if not user_info:
        logger.warning("Invalid Google token attempted")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )
    
    # Find or create user
    user = db.query(User).filter(User.email == user_info["email"]).first()
    
    if not user:
        # ✅ Create new user from Google
        user = User(
            email=user_info["email"],
            full_name=user_info.get("name", ""),
            auth_provider="google",
            provider_id=user_info["id"],
            is_email_verified=user_info.get("email_verified", False),
            hashed_password="oauth",  # Placeholder - OAuth users don't have passwords
            created_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"New user created via Google: {user.email}")
    else:
        # Update existing user
        user.last_login = datetime.utcnow()
        user.auth_provider = "google"  # Link to Google account
        db.commit()
        logger.info(f"User {user.email} logged in via Google")
    
    # ✅ Create token pair
    token_pair = TokenManager.create_token_pair(user_id=user.id, email=user.email)
    
    return {
        "access_token": token_pair.access_token,
        "refresh_token": token_pair.refresh_token,
        "token_type": "bearer",
        "expires_in": token_pair.expires_in,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.full_name
        }
    }


# ============================================
# ✅ NEW: GitHub Sign-In Endpoint (Optional)
# ============================================
@app.post("/api/auth/github")
async def github_signin(code: str, state: str, db: Session = Depends(get_db)):
    """
    Authenticate with GitHub using authorization code
    
    This is handled server-side for security
    """
    # TODO: Implement GitHub OAuth flow
    # See GitHubOAuthHandler in serverapp/auth/oauth.py
    pass
```

---

## 5. UPDATE DATABASE MODELS

In `serverapp/database/models.py`, update the User model:

### FIND THIS:
```python
class User(Base):
    """Authenticated user model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
```

### REPLACE WITH THIS:
```python
class User(Base):
    """Authenticated user model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # ✅ CHANGED: nullable for OAuth users
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # ✅ NEW: OAuth fields
    auth_provider = Column(String, default="local")  # 'local', 'google', 'github'
    provider_id = Column(String, nullable=True)  # ID from OAuth provider
    is_email_verified = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)  # Optional: for brute force detection
    locked_until = Column(DateTime, nullable=True)  # Optional: for account locking
```

---

## 6. UPDATE .env FILE

Create `.env` file from `.env.example`:

```bash
# Copy .env.example
cp .env.example .env

# Edit .env and add:

# Google OAuth2 Credentials
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Secret key (generate random value)
SECRET_KEY=your-random-secret-key-min-32-characters-long

# Token expiration
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Rate limiting
RATE_LIMIT_REQUESTS=5
RATE_LIMIT_PERIOD=900
```

---

## 7. MIGRATION SQL (if using Alembic)

```sql
-- Add columns to users table for OAuth support

ALTER TABLE users
ADD COLUMN IF NOT EXISTS auth_provider VARCHAR(50) DEFAULT 'local',
ADD COLUMN IF NOT EXISTS provider_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS last_login TIMESTAMP,
ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS failed_login_attempts INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP;

-- Make hashed_password nullable for OAuth users
ALTER TABLE users
ALTER COLUMN hashed_password DROP NOT NULL;

-- Create index for OAuth lookups
CREATE INDEX IF NOT EXISTS idx_users_provider_id ON users(provider_id);
```

---

## TESTING THE CHANGES

### 1. Test Password Validation
```bash
# Should FAIL - weak password
curl -X POST http://localhost:8000/api/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"weak","full_name":"Test","phone":"1234567890"}'
# Response: "Password must contain at least one uppercase letter"

# Should SUCCEED - strong password
curl -X POST http://localhost:8000/api/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Strong123!","full_name":"Test","phone":"1234567890"}'
# Response: {access_token, refresh_token, user}
```

### 2. Test Rate Limiting
```bash
# Try 6 rapid logins (should be blocked on 6th)
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/login/json \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"Strong123!"}'
done
# 6th attempt returns: 429 Too Many Requests
```

### 3. Test Token Refresh
```bash
# Get tokens from login
TOKEN_RESPONSE=$(curl -X POST http://localhost:8000/api/login/json \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Strong123!"}')

# Extract refresh_token
REFRESH_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"refresh_token":"[^"]*' | cut -d'"' -f4)

# Refresh the token
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}"
# Response: {access_token, refresh_token, expires_in}
```

---

## SUMMARY

✅ **Changes Required:**
1. Add imports at top of server.py
2. Replace signup endpoint
3. Replace login endpoint
4. Add 3 new endpoints (refresh, google signin, github signin)
5. Update User model in database/models.py
6. Create .env with Google OAuth credentials
7. Run database migration

✅ **Files to Create (Already Done):**
- `serverapp/auth/password.py`
- `serverapp/auth/rate_limit.py`
- `serverapp/auth/tokens.py`
- `serverapp/auth/oauth.py`
- Supporting files

✅ **Testing:**
- Test weak password rejection
- Test rate limiting
- Test token refresh
- Test Google Sign-In (after setup)

---

That's it! Once integrated, your authentication system will:
- ✅ Enforce strong passwords
- ✅ Block brute force attacks
- ✅ Use secure token refresh flow
- ✅ Support Google Sign-In
- ✅ Follow OAuth2 best practices
