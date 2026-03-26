# Authentication Security Implementation Guide

**Date:** February 9, 2026
**Phase:** Security Hardening + OAuth2 Integration

---

## SUMMARY OF IMPROVEMENTS

### ✅ What's Been Implemented

#### 1. **Enhanced Password Validation** (`serverapp/auth/password.py`)
- ✓ Minimum 8 characters
- ✓ At least 1 uppercase letter (A-Z)
- ✓ At least 1 number (0-9)
- ✓ At least 1 special character (!@#$%^&* etc.)
- ✓ Password strength scoring (0-100)
- ✓ User feedback on password improvements

**Usage:**
```python
from auth.password import PasswordValidator

# Validate password
is_valid, error_msg = PasswordValidator.validate("MyPass123!")
if not is_valid:
    print(f"❌ {error_msg}")

# Get strength score
score = PasswordValidator.get_strength_score("MyPass123!")
print(f"Strength: {score}/100")

# Get improvement feedback
feedback = PasswordValidator.get_feedback("weak")
for item in feedback:
    print(f"  • {item}")
```

#### 2. **Rate Limiting** (`serverapp/auth/rate_limit.py`)
- ✓ Prevent brute force attacks on login/signup
- ✓ In-memory rate limiter (can be upgraded to Redis)
- ✓ Per-IP rate limiting
- ✓ Configurable attempts and time windows

**Default Limits:**
- Login: 5 attempts per 15 minutes
- Signup: 3 attempts per day
- Password reset: 10 attempts per day

**Usage:**
```python
from auth.rate_limit import rate_limit

@app.post("/api/login/json")
@rate_limit(max_attempts=5, window_seconds=900)  # 5 attempts in 15 mins
def login(request: Request, user_login: UserLogin, db: Session = Depends(get_db)):
    # Your login logic
    pass
```

#### 3. **Token Management with Refresh Tokens** (`serverapp/auth/tokens.py`)
- ✓ Short-lived access tokens (15 minutes)
- ✓ Long-lived refresh tokens (7 days)
- ✓ Token encryption and validation
- ✓ Token pair generation (both access + refresh)
- ✓ Token expiration checking

**Usage:**
```python
from auth.tokens import TokenManager, Token

# Create token pair
token_pair: Token = TokenManager.create_token_pair(
    user_id=user.id,
    email=user.email
)

# Returns:
# {
#     "access_token": "eyJ0eXAi...",
#     "refresh_token": "eyJ0eXAi...",
#     "token_type": "bearer",
#     "expires_in": 900  # 15 minutes in seconds
# }

# Validate token
is_valid, payload = TokenManager.validate_access_token(access_token)
```

#### 4. **OAuth2 Social Login** (`serverapp/auth/oauth.py`)
- ✓ Google Sign-In ready
- ✓ GitHub authentication ready
- ✓ Email verification from providers
- ✓ User profile picture support

**Supported:**
- ✓ Google OAuth2 (ID token verification)
- ✓ GitHub OAuth2
- 🏗️ Facebook (can add)
- 🏗️ Apple Sign-In (can add)

---

## QUICK START IMPLEMENTATION

### Step 1: Update Backend (server.py)

Add these new endpoints to your `server.py`:

```python
from fastapi import Request
from auth import TokenManager, PasswordValidator, rate_limit, GoogleOAuthHandler
from auth.oauth import GoogleSignInRequest
import logging

logger = logging.getLogger(__name__)

# 1. Enhanced Sign-up with password validation
@app.post("/api/signup", response_model=dict)
async def signup(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    """
    Create new user with password validation
    """
    # Validate password strength
    is_valid, error_msg = PasswordValidator.validate(user.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Check if email exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
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
    
    # Create token pair
    token_pair = TokenManager.create_token_pair(user_id=new_user.id, email=new_user.email)
    
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


# 2. Enhanced Login with rate limiting
@app.post("/api/login/json")
@rate_limit(max_attempts=5, window_seconds=900)
async def login(request: Request, user_login: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email/password - RATE LIMITED
    """
    client_ip = request.client.host
    
    user = db.query(User).filter(User.email == user_login.email).first()
    if not user or not verify_password(user_login.password, user.hashed_password):
        # Log failed attempt
        logger.warning(f"Failed login attempt for {user_login.email} from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create token pair
    token_pair = TokenManager.create_token_pair(user_id=user.id, email=user.email)
    
    logger.info(f"User {user.email} logged in from {client_ip}")
    
    return {
        "access_token": token_pair.access_token,
        "refresh_token": token_pair.refresh_token,
        "token_type": "bearer",
        "expires_in": token_pair.expires_in
    }


# 3. Refresh Token Endpoint
@app.post("/api/auth/refresh")
def refresh_token(request: dict, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token
    """
    refresh_token = request.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Refresh token required"
        )
    
    # Validate refresh token
    is_valid, payload = TokenManager.validate_refresh_token(refresh_token)
    
    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )
    
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Create new token pair
    token_pair = TokenManager.create_token_pair(user_id=user.id, email=user.email)
    
    return {
        "access_token": token_pair.access_token,
        "refresh_token": token_pair.refresh_token,
        "token_type": "bearer",
        "expires_in": token_pair.expires_in
    }


# 4. Google Sign-In Endpoint
@app.post("/api/auth/google")
async def google_signin(google_request: GoogleSignInRequest, db: Session = Depends(get_db)):
    """
    Authenticate with Google ID token
    """
    # Verify Google token
    user_info = await GoogleOAuthHandler.verify_id_token(
        id_token=google_request.id_token,
        client_id=settings.google_client_id  # Set in .env
    )
    
    if not user_info:
        raise HTTPException(
            status_code=401,
            detail="Invalid Google token"
        )
    
    # Find or create user
    user = db.query(User).filter(User.email == user_info["email"]).first()
    
    if not user:
        # Create new user from Google
        user = User(
            email=user_info["email"],
            full_name=user_info.get("name", ""),
            auth_provider="google",
            provider_id=user_info["id"],
            is_email_verified=user_info.get("email_verified", False),
            hashed_password="oauth"  # Placeholder
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"New user created via Google: {user.email}")
    else:
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
    
    # Create token pair
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
```

### Step 2: Update Database Models (database/models.py)

Add new fields to the User model:

```python
class User(Base):
    """Authenticated user model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # NEW: OAuth fields
    auth_provider = Column(String, default="local")  # 'local', 'google', 'github'
    provider_id = Column(String, nullable=True)  # ID from provider
    is_email_verified = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
```

### Step 3: Update .env

Add Google OAuth credentials:

```bash
# Google OAuth2
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

### Step 4: Frontend Setup

Update `frontend/src/pages/Login.tsx` (use the provided Login.new.tsx as template)

Key changes:
- Add Google Sign-In button
- Display password requirements
- Use refresh token flow
- Store tokens securely

---

## SECURITY BEST PRACTICES

### Token Storage
```typescript
// ✅ GOOD: Use httpOnly cookie (secure against XSS)
// Backend sets:
// Set-Cookie: access_token=...; HttpOnly; Secure; SameSite=Strict

// Store refresh token in httpOnly cookie
// ⚠️ AVOID: localStorage for sensitive tokens
```

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://www.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### Security Headers
```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

---

## TESTING CHECKLIST

- [ ] Weak passwords are rejected
- [ ] Strong passwords are accepted
- [ ] Rate limiting blocks repeated login attempts
- [ ] Access token expires in 15 minutes
- [ ] Refresh token extends session for 7 days
- [ ] Google Sign-In button works (after setup)
- [ ] User can refresh expired token
- [ ] Logout clears tokens
- [ ] CSRF protection active
- [ ] Security headers present

---

## NEXT STEPS

### Immediate (Today)
1. ✅ Implement password validation
2. ✅ Add rate limiting
3. ✅ Implement token refresh
4. ✅ Add OAuth2 handlers

### Short-term (This Week)
1. Setup Google Cloud Console credentials
2. Integrate Google Sign-In in frontend
3. Test the entire auth flow
4. Deploy to production

### Long-term (Next)
1. Add GitHub OAuth
2. Implement 2FA/TOTP
3. Add email verification
4. Setup monitoring/alerting

---

## TROUBLESHOOTING

**Q: Google Sign-In shows "setup required"**  
A: Set `GOOGLE_CLIENT_ID` in .env file. Get credentials from Google Cloud Console.

**Q: Rate limiting blocks all requests**  
A: Check IP detection. In Docker/proxy, set trusted proxy headers.

**Q: Refresh token doesn't work**  
A: Ensure refresh token is sent in request body, not header.

**Q: Password validation too strict**  
A: Adjust `MIN_LENGTH`, `REQUIRE_UPPERCASE` etc. in `auth/password.py`

---

For questions or issues, refer to the code inline documentation.
