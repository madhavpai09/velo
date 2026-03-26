# Authentication System Architecture

## Current vs Enhanced Flow

### BEFORE (Current System - Issues)
```
User                              Backend                         Storage
 │                                  │                               │
 ├─ Email + Password ──────────────>│                               │
 │                                  ├─ No validation            × WEAK
 │                                  ├─ Check database           
 │                                  │  
 │                                  ├─ Create JWT ────────────────>│ Token
 │                                  │  (30 days)                × Long
 │<─ Return JWT ─────────────────────┤                              │
 │                                  │                               │
 ├─ Store in localStorage ─────────────────────────────────────────┼──> localStorage
 │ (XSS vulnerable)            × INSECURE             × Exposed
 │
 ├─ API calls with JWT in header
 │  (Attacker can steal from localStorage)
```

### AFTER (Enhanced System - Secure)
```
User                              Backend                         Storage
 │                                  │                               │
 ├─ Email + Strong Password ──────>│                               │
 │  (Validated: 8+ chars)           ├─ Validate password strength  ✓ CHECKED
 │                                  │  ├─ Must have uppercase
 │                                  │  ├─ Must have number
 │                                  │  ├─ Must have special char
 │                                  │  
 │                                  ├─ Check rate limit            ✓ PROTECTED
 │                                  │  (5 attempts per 15 min)
 │                                  │  
 │                                  ├─ Create token PAIR:
 │                                  │  ├─ Access Token (15 min)    ✓ Short-lived
 │                                  │  └─ Refresh Token (7 days)   ✓ Secure
 │<─ Return tokens ────────────────-┤                              │
 │                                  │                              │
 ├─ Store in httpOnly cookie ───────────────────────────────────┬──> httpOnly
 │  (XSS-safe storage)              ✓ SECURE                   │  (Inaccessible
 │                                                               │   to JS)
 ├─ API calls with Access Token (header)
 │  
 │  (After 15 minutes, token expires)
 │
 ├─ POST /api/auth/refresh ────────>│                               │
 │  (with refresh token)             ├─ Validate refresh token    ✓ Checked
 │                                  ├─ Create new access token
 │<─ New access token ──────────────-┤
 │
 └─ Continue API calls (no re-login needed)
```

---

## OAuth2 Social Login Flow

### Google Sign-In Sequence
```
Frontend (React)          Google          Backend (FastAPI)      Database
    │                      │                   │                    │
    ├─ User clicks "Sign in with Google"
    │
    ├─────────────────────────────────────> Google Auth Screen
    │                                         │
    │<────────────────────────────────────── ID Token (JWT)
    │
    ├─ ID Token ──────────────────────────────>│
    │                                         ├─ Verify with Google
    │                                         ├─ Extract email, name, picture
    │                                         │
    │                                         ├─ Check if user exists
    │                                         │  │
    │                                         │  └─> Database
    │                                         │       │
    │                                         ├─ If new: Create user
    │                                         │  ├─ email: user's google email
    │                                         │  ├─ name: google name
    │                                         │  ├─ auth_provider: "google"
    │                                         │  ├─ provider_id: google ID
    │                                         │
    │                                         ├─ Create access + refresh tokens
    │<────────────────────────────────────────┤
    │                                         
    ├─ Store tokens securely (httpOnly cookie)
    │
    └─ Redirect to /ride (logged in!)
```

### GitHub Sign-In (Similar Flow)
```
Frontend                  GitHub         Backend              Database
  │                        │               │                    │
  └─ Authorization Code ────> GitHub API ──> Verify & Get User Info
                                           │ (email, name, avatar)
                                           │
                                           └─> Find/Create User
                                           │
                                           └─> Generate Tokens
```

---

## Detailed Component Architecture

### 1. Password Validation Module
```
Input: "MyPassword123!"
    │
    ├─ Check length >= 8          ✓ Yes (14 chars)
    ├─ Check has uppercase        ✓ Yes (M, P)
    ├─ Check has number           ✓ Yes (1, 2, 3)
    ├─ Check has special char     ✓ Yes (!)
    │
    └─ Result: ✅ VALID
                Score: 95/100
```

### 2. Rate Limiting Architecture
```
Request: Login attempt from 192.168.1.100

Rate Limiter
    │
    ├─ Generate key: "/api/login:192.168.1.100"
    ├─ Check attempt history
    │   ├─ Last 15 minutes: [10:00, 10:02, 10:05]  (3 attempts)
    │   ├─ Allowed: 5 attempts
    │   ├─ Remaining: 2 attempts
    │
    └─ Result: ✅ ALLOWED (but only 2 more in this window)

After 5 attempts:
    └─ Result: ❌ BLOCKED
       Message: "Too many attempts. Try again in X seconds"
       Status: 429 (Too Many Requests)
```

### 3. Token System Architecture
```
Access Token (15 minutes)
├─ Claims:
│  ├─ sub: user_email
│  ├─ exp: 1707514200  (15 min from now)
│  ├─ iat: 1707513300  (issued at)
│  ├─ type: "access"
│  └─ aud: "api.velo.com"
├─ Signature: HMAC-SHA256
└─ Use: All API requests

Refresh Token (7 days)
├─ Claims:
│  ├─ sub: user_id
│  ├─ exp: 1708119300  (7 days from now)
│  ├─ iat: 1707514200  (issued at)
│  ├─ type: "refresh"
│  ├─ jti: unique_token_id
│  └─ aud: "api.velo.com"
├─ Signature: HMAC-SHA256
└─ Use: Get new access token when expired

Flow:
1. User logs in
2. Get access token + refresh token
3. Use access token for 15 minutes
4. When expired, use refresh token to get new access token
5. Refresh token valid for 7 days
6. After 7 days, must login again
```

### 4. OAuth2 Security
```
Verification Steps:
1. Frontend: User clicks "Sign with Google"
   └─ Redirected to Google auth screen
   
2. User: Logs in with Google credentials
   └─ Google verifies password (not your app)
   
3. Google: Returns ID Token (JWT signed by Google)
   └─ Contains: user_id, email, name, picture
   
4. Frontend: Sends ID Token to backend
   └─ POST /api/auth/google { id_token: "..." }
   
5. Backend: Verify ID Token
   ├─ Check signature (Google's public key)
   ├─ Check "aud" (client_id) matches ours
   ├─ Check "exp" (not expired)
   └─ If all valid: ✅ Trust the user info
   
6. Backend: Create/find user in database
   └─ If email matches: Use existing account
   └─ If new email: Create account automatically
   
7. Backend: Generate access + refresh tokens
   └─ Return to frontend
   
8. Frontend: Store tokens securely
   └─ User is logged in!

Security Benefits:
✅ Google handles password security (not you)
✅ ID Token is signed (can't be faked)
✅ Signature verification is cryptographic
✅ Standard OAuth2 protocol
✅ Both parties are verified
```

---

## Endpoint Mapping

### Authentication Endpoints

| Method | Endpoint | Purpose | Rate Limit | Response |
|--------|----------|---------|-----------|----------|
| POST | `/api/signup` | Create account with email/password | 3/day | `{access_token, refresh_token, user}` |
| POST | `/api/login/json` | Login with email/password | 5/15min | `{access_token, refresh_token}` |
| POST | `/api/auth/google` | Login/signup with Google | None | `{access_token, refresh_token, user}` |
| POST | `/api/auth/github` | Login/signup with GitHub | None | `{access_token, refresh_token, user}` |
| POST | `/api/auth/refresh` | Get new access token | None | `{access_token, expires_in}` |
| GET | `/api/me` | Get current user info | None | `{id, email, name, phone}` |

---

## Security Headers

```python
# Automatically added to all responses
Response Headers:
├─ X-Frame-Options: DENY
│  └─ Prevents clickjacking attacks
├─ X-Content-Type-Options: nosniff
│  └─ Prevents MIME sniffing
├─ X-XSS-Protection: 1; mode=block
│  └─ Enables XSS protection in browsers
├─ Strict-Transport-Security: max-age=31536000
│  └─ Forces HTTPS only
└─ Set-Cookie: ... HttpOnly; Secure; SameSite=Strict
   └─ Makes token inaccessible to JavaScript
```

---

## Database Schema Changes

```sql
-- User table enhancements
ALTER TABLE users 
ADD COLUMN auth_provider VARCHAR(50) DEFAULT 'local',
ADD COLUMN provider_id VARCHAR(255),
ADD COLUMN last_login TIMESTAMP,
ADD COLUMN is_email_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN failed_login_attempts INT DEFAULT 0,
ADD COLUMN locked_until TIMESTAMP;

-- Optional: Token audit log
CREATE TABLE auth_audit (
    id SERIAL PRIMARY KEY,
    user_id INT,
    event_type VARCHAR(50),  -- 'login', 'failed_login', 'token_refresh'
    ip_address VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Optional: Refresh token tracking
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    jti VARCHAR(255) NOT NULL,  -- JWT ID
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,  -- NULL if not revoked
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Error Handling

### Common Error Responses

```json
// Weak password error (400)
{
  "detail": "Password must contain at least one uppercase letter"
}

// Rate limit exceeded (429)
{
  "detail": "Too many attempts. Try again in 745 seconds.",
  "retry_after": 745
}

// Invalid credentials (401)
{
  "detail": "Incorrect email or password"
}

// Invalid token (401)
{
  "detail": "Invalid or expired token"
}

// Invalid Google token (401)
{
  "detail": "Invalid Google token"
}

// Email already registered (400)
{
  "detail": "Email already registered"
}
```

---

## Performance Metrics

```
Operation                          Latency      Impact
────────────────────────────────────────────────────────
Password strength check            <1ms         Negligible
Rate limiter check                 <1ms         Negligible
bcrypt password hashing            ~100ms       One-time (login only)
JWT token creation                 <1ms         Minimal
JWT token validation               ~5ms         Per request
Google OAuth2 verification         ~200ms       One-time (login only)
Database user lookup               ~10ms        Per request
─────────────────────────────────────────────────────────
Total login time                   ~300-400ms   Acceptable
Total API request overhead         ~5ms         Negligible
```

---

## Deployment Checklist

- [ ] Update `.env` with `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
- [ ] Run database migrations to add new User fields
- [ ] Update frontend dependencies (`npm install`)
- [ ] Update backend dependencies (`pip install -r requirements.txt`)
- [ ] Test password validation (weak password should fail)
- [ ] Test rate limiting (5 rapid logins should fail)
- [ ] Test Google Sign-In (requires Google Cloud setup)
- [ ] Test token refresh (after 15 minutes)
- [ ] Verify httpOnly cookies are set (check headers)
- [ ] Run security headers check (curl -I)
- [ ] Test CORS with specific origin
- [ ] Monitor logs for suspicious activity

---

Created: February 9, 2026
For: Mini Uber (VELO) Production Deployment
