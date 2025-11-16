# 🚀 How to Restart Mini Uber System

## Quick Start (3 Steps)

### Step 1: Start Backend Servers
Run the startup script:
```bash
cd /Users/jmadhavpai/Desktop/mini_uber
./start_servers.sh
```

This will open 3 terminal windows automatically:
- **Terminal 1**: Main Server (port 8000)
- **Terminal 2**: Matcher Service (port 8001)  
- **Terminal 3**: Notifier Service (port 8002)

### Step 2: Start Frontend
Open a new terminal and run:
```bash
cd /Users/jmadhavpai/Desktop/mini_uber/frontend
npm run dev
```

The frontend will be available at: `http://localhost:5173`

### Step 3: Test the System
1. Open `http://localhost:5173` in your browser
2. Choose "I'm a User" or "I'm a Driver"
3. Start using the app!

---

## Manual Start (If Script Doesn't Work)

### Terminal 1: Main Server
```bash
cd /Users/jmadhavpai/Desktop/mini_uber/serverapp
python server.py
```
**Expected output**: `Orchestrator running on port 8000`

### Terminal 2: Matcher Service
```bash
cd /Users/jmadhavpai/Desktop/mini_uber/serverapp
python server_matcher.py
```
**Expected output**: `Matcher running on port 8001`

### Terminal 3: Notifier Service
```bash
cd /Users/jmadhavpai/Desktop/mini_uber/serverapp
python server_notifier.py
```
**Expected output**: `Notifier running on port 8002`

### Terminal 4: Frontend
```bash
cd /Users/jmadhavpai/Desktop/mini_uber/frontend
npm run dev
```
**Expected output**: `Local: http://localhost:5173`

---

## Verification Checklist

✅ **All 3 backend servers running:**
- Main Server: `http://localhost:8000` → Should show `{"message": "Orchestrator running on port 8000"}`
- Matcher: `http://localhost:8001` → Should show `{"message": "Matcher running on port 8001"}`
- Notifier: `http://localhost:8002` → Should show `{"message": "Notifier running on port 8002"}`

✅ **Frontend running:**
- Open `http://localhost:5173` → Should show landing page with "I'm a User" and "I'm a Driver" options

---

## Troubleshooting

### Port Already in Use
If you get "port already in use" error:
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9  # For port 8000
lsof -ti:8001 | xargs kill -9  # For port 8001
lsof -ti:8002 | xargs kill -9  # For port 8002
lsof -ti:5173 | xargs kill -9  # For frontend port
```

### Database Connection Issues
Make sure PostgreSQL is running:
```bash
# Check if PostgreSQL is running (macOS)
brew services list | grep postgresql
# Or start it:
brew services start postgresql
```

### Python Dependencies
If you get import errors:
```bash
cd /Users/jmadhavpai/Desktop/mini_uber/serverapp
pip install -r requirements.txt
```

### Frontend Dependencies
If frontend doesn't start:
```bash
cd /Users/jmadhavpai/Desktop/mini_uber/frontend
npm install
```

---

## Testing the System

### Test as User:
1. Go to `http://localhost:5173`
2. Click "I'm a User"
3. Enter User ID (e.g., `6000`)
4. Click "Set ID"
5. Click on map to select pickup location
6. Click again to select dropoff location
7. Click "Request Ride"

### Test as Driver:
1. Go to `http://localhost:5173`
2. Click "I'm a Driver"
3. Enter Driver ID (e.g., `9000`) and Name
4. Click "Register as Driver"
5. Click "🟢 Go Online"
6. Wait for ride assignments (polling every 2 seconds)

---

## Order of Operations

**IMPORTANT**: Start servers in this order:
1. ✅ Main Server (port 8000)
2. ✅ Matcher Service (port 8001)
3. ✅ Notifier Service (port 8002)
4. ✅ Frontend (port 5173)

The backend servers can be started in any order, but it's best to start Main Server first.

---

## Quick Commands Reference

```bash
# Start all servers (macOS)
./start_servers.sh

# Start frontend
cd frontend && npm run dev

# Check if servers are running
curl http://localhost:8000  # Main server
curl http://localhost:8001  # Matcher
curl http://localhost:8002  # Notifier

# Kill all Python processes (if needed)
pkill -f "python.*server"
```

---

## What Each Service Does

- **Main Server (8000)**: Handles API requests, driver registration, ride requests
- **Matcher (8001)**: Matches pending rides with available drivers
- **Notifier (8002)**: Notifies users and drivers about matches
- **Frontend (5173)**: Web interface for users and drivers

All services must be running for the system to work properly!

