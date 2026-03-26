# Authentication Security Audit & Enhancement Plan

**Date:** February 9, 2026
**Application:** VELO - Mini Uber

---

## I. CURRENT AUTH SYSTEM ANALYSIS

### What's Implemented ✅
- JWT token-based authentication
- Bcrypt password hashing
- Email/password signup and login
- Bearer token in Authorization header
- User profile verification endpoint

### Security Issues Identified 🔴

| Severity | Issue | Problem | Impact | Fix |
|----------|-------|---------|--------|-----|
| 🟠 **HIGH** | Token in localStorage | Vulnerable to XSS attacks | Attacker can steal sessions | Use HttpOnly cookies + CSRF protection |
| 🟠 **HIGH** | No password validation | Users can set weak passwords | Account takeover risk | Enforce minimum strength |
| 🟠 **HIGH** | No rate limiting | Brute force attacks possible | Account compromise | Add rate limiting to auth endpoints |
| 🟡 **MEDIUM** | Long token expiry (30 days) | If token leaked, long exposure | Account compromise | Use short-lived tokens + refresh tokens |
| 🟡 **MEDIUM** | No CSRF protection | CSRF attacks possible | Session hijacking | Add CSRF token validation |
| 🟢 **LOW** | No 2FA/MFA | Single factor only | Compromised if password leaked | Add optional TOTP 2FA |

---

## II. SECURITY IMPROVEMENTS (IMMEDIATE)

### 1. **PASSWORD VALIDATION**
- Minimum 8 characters
- At least one uppercase letter
- At least one number
- At least one special character

### 2. **RATE LIMITING**
- Max 5 login attempts per 15 minutes per IP
- Max 3 signup attempts per day per IP
- Max 10 password reset requests per day per email

### 3. **TOKEN SECURITY**
- Access token: 15 minutes expiry
- Refresh token: 7 days expiry
- Use secure httpOnly cookies for tokens
- CSRF token in headers

### 4. **CORS & SECURITY HEADERS**
- Restrict CORS to specific origins only (not *)
- Add HTTP security headers (HSTS, CSP, X-Frame-Options)

---

## III. OAUTH2 SOCIAL LOGIN (RECOMMENDED)

### Benefits
✅ Users don't need to remember passwords  
✅ Reduce signup friction  
✅ Security delegated to trusted providers  
✅ Built-in 2FA support  
✅ Standardized protocol  

### Supported Providers
- **Google** (most popular)
- **GitHub** (developers)
- **Facebook** (optional)

### Implementation Architecture

```
Frontend (React)                Backend (FastAPI)           Provider (Google)
   │                               │                           │
   ├─ Click "Login with Google"    │                           │
   │                               │                           │
   ├────────────────────────────────────────── OAuth2 Flow ───────>
   │                               │                           │
   │                       <─── Authorization Code ───────────
   │                               │                           │
   │   Exchange Code + Client │                           
   │   Secret for Token at    │                           
   │   /api/auth/callback     │                           
   │                               │ POST with code ────────────>
   │                               │ GET user info ─────────────>
   │                               │           <─ User Data ────
   │                               │                           │
   │        <─── Return JWT & User ───                         
   │                               │                           
   └─ Store token in httpOnly      │                           
      cookie + localStorage        │                           
```

### Setup Steps

1. **Google Cloud Console Setup**
   - Create OAuth2 credentials
   - Add redirect URIs
   - Get Client ID and Client Secret

2. **Backend Implementation**
   - `python-multipart` - for form data
   - `authlib` or `google-auth` - for OAuth2 verification
   - New endpoints:
     - `POST /api/auth/google` - Verify Google token
     - `POST /api/auth/callback` - Handle OAuth2 callback
     - `POST /api/auth/refresh` - Refresh token

3. **Frontend Implementation**
   - `@react-oauth/google` - Google sign-in button
   - Update login/signup pages
   - Handle token storage securely

---

## IV. IMPLEMENTATION ROADMAP

### Phase 1: Immediate Fixes (TODAY)
1. ✅ Add password validation
2. ✅ Add rate limiting to auth endpoints
3. ✅ Implement refresh token mechanism
4. ✅ Add CSRF protection
5. ✅ Secure token storage (httpOnly cookies)

### Phase 2: OAuth2 Integration (NEXT)
1. Create OAuth2 service module
2. Implement Google Sign-In
3. Update frontend login/signup UI
4. Testing and security audit

### Phase 3: Additional Security (OPTIONAL)
1. Implement 2FA/TOTP
2. Add device tracking
3. Email verification
4. Password reset flow

---

## V. DATABASE CHANGES NEEDED

```sql
-- Add fields for OAuth2
ALTER TABLE users ADD COLUMN auth_provider VARCHAR(50) DEFAULT 'local';  -- 'local', 'google', 'github'
ALTER TABLE users ADD COLUMN provider_id VARCHAR(255);  -- ID from provider
ALTER TABLE users ADD COLUMN last_login TIMESTAMP;
ALTER TABLE users ADD COLUMN failed_login_attempts INT DEFAULT 0;
ALTER TABLE users ADD COLUMN locked_until TIMESTAMP;
ALTER TABLE users ADD COLUMN is_email_verified BOOLEAN DEFAULT FALSE;

-- Add refresh token tracking
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(500) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Add audit log for login attempts
CREATE TABLE auth_audit (
    id SERIAL PRIMARY KEY,
    user_id INT,
    event_type VARCHAR(50),  -- 'login', 'failed_login', 'logout'
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## VI. CODE CHANGES SUMMARY

### Files to Create
- `serverapp/auth/password.py` - Password validation
- `serverapp/auth/oauth.py` - OAuth2 handler
- `serverapp/auth/rate_limit.py` - Rate limiting
- `serverapp/auth/tokens.py` - Token management

### Files to Modify
- `serverapp/server.py` - Add new endpoints
- `serverapp/database/models.py` - Add new fields
- `frontend/src/pages/Login.tsx` - Add OAuth button
- `frontend/src/pages/Signup.tsx` - Add OAuth option
- `frontend/src/context/AuthContext.tsx` - Secure token storage

---

## VII. TESTING CHECKLIST

- [ ] Password validation works (weak passwords rejected)
- [ ] Rate limiting blocks excessive attempts
- [ ] Tokens expire correctly
- [ ] Refresh token flow works
- [ ] Google OAuth sign-in works
- [ ] CSRF protection prevents attacks
- [ ] HttpOnly cookies set correctly
- [ ] Session persists across page reloads
- [ ] Logout clears tokens
- [ ] Concurrent requests don't cause issues

---

**Recommendation:** Start with Phase 1 (immediate fixes) today, then add OAuth2 in Phase 2. The current system is functional but needs security hardening.
