# 🔧 "Load failed" Error - Fix Guide

## Problem
You're seeing a "Load failed" error when trying to sign up. This means the frontend is trying to contact the backend API but failing.

## Root Causes
1. ❌ Backend server is not running
2. ❌ Backend dependencies are not installed
3. ❌ Environment configuration is missing
4. ❌ Database is not connected

## Solution (Step by Step)

### Step 1: Install Dependencies
```bash
cd /Users/jmadhavpai/work/mini_uber
pip install -r serverapp/requirements.txt
```

### Step 2: Setup Environment Variables
```bash
# Copy template
cp .env.example .env

# Edit .env and add these (at minimum):
GOOGLE_CLIENT_ID=temp_placeholder_for_now
DATABASE_URL=postgresql://user:password@localhost/mini_uber
# Or use SQLite for testing: DATABASE_URL=sqlite:///./test.db
```

### Step 3: Start the Backend Server
**Option A: Using the startup script**
```bash
chmod +x start_backend.sh
./start_backend.sh
```

**Option B: Manual start**
```bash
cd serverapp
python3 -m uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
Uvicorn running on http://127.0.0.1:8000
```

### Step 4: Verify Backend is Running
```bash
# In another terminal, test the health endpoint
curl http://localhost:8000/api/health

# Expected response:
# {"message":"Mini Uber API v3 - WORKING"}
```

### Step 5: Check Frontend Configuration
Make sure your frontend is configured to use the correct backend URL.

Edit `frontend/src/utils/api.ts` (or wherever API calls are made):
```typescript
const BASE_URL = 'http://localhost:8000';
// or
const BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';
```

### Step 6: Start Frontend
```bash
cd frontend
npm run dev
# Visit http://localhost:5173
```

## Testing the Signup Form

Now when you try to signup:
1. Go to http://localhost:5173
2. Click "Sign Up"
3. Enter test data:
   - Email: test@example.com
   - Name: Test Driver
   - Phone: 9876543210
   - Password: MyStr0ng@Pass

**Expected:**
- If password is weak (e.g., "password"): Error message "Password must be at least 8 characters..."
- If password is strong: Successfully signed up, redirected to dashboard

## Verification Checklist

- [ ] Backend server is running (`uvicorn` shows "Uvicorn running on...")
- [ ] Frontend is running (`npm run dev` shows "Local:...")
- [ ] Can access http://localhost:8000 in browser
- [ ] Can access http://localhost:5173 in browser
- [ ] Can call signup API: `curl -X POST http://localhost:8000/api/signup -H "Content-Type: application/json" -d '{"email":"test@example.com","password":"MyPassword123","full_name":"Test","phone":"123456"}'`

## Debug: Check Logs

**Backend logs:**
- Look for uvicorn startup messages
- Look for any import errors
- Look for CORS issues

**Frontend logs:**
- Open browser DevTools (F12)
- Check Console tab for errors
- Check Network tab to see API calls

### Common Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| "Connection refused" | Backend not running | Run `python3 -m uvicorn serverapp.server:app --reload` |
| "ModuleNotFoundError" | Dependencies not installed | Run `pip install -r serverapp/requirements.txt` |
| "CORS error" | Frontend and backend domains differ | Check CORS middleware in server.py |
| "Load failed" | API request failed | Check backend is running and logs |

## Quick Test Commands

```bash
# Test backend is running
curl http://localhost:8000/

# Test signup endpoint exists
curl -X POST http://localhost:8000/api/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "MyP@ssw0rd123",
    "full_name": "Test User",
    "phone": "9876543210"
  }'

# Expected success response:
# {
#   "access_token": "eyJ0eXAi...",
#   "refresh_token": "eyJ0eXAi...",
#   "token_type": "bearer"
# }
```

## Need More Help?

1. Check [START_HERE.md](START_HERE.md) for step-by-step setup
2. Check [AUTH_QUICK_REFERENCE.md](AUTH_QUICK_REFERENCE.md) for API details
3. Review backend logs while making signup request
4. Check browser Network tab to see the actual API response

---

**After you start the backend server with `./start_backend.sh`, the "Load failed" error should go away!**
