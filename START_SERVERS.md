# 🚀 How to Run Mini Uber System

## Required Services

You need to run **5 types of services**:

### 1. Server Services (Keep these running always)

These are the backend services that handle matching and notifications:

```bash
# Terminal 1: Main Orchestrator Server (Port 8000)
cd serverapp
python server.py

# Terminal 2: Matcher Service (Port 8001)
cd serverapp
python server_matcher.py

# Terminal 3: Notifier Service (Port 8002)
cd serverapp
python server_notifier.py
```

### 2. Driver Clients (Keep at least 1 running)

Drivers wait for ride assignments. You can run multiple drivers on different ports:

```bash
# Terminal 4: Driver 1 (Port 9000)
cd client
python driver_client.py --port 9000

# Terminal 5: Driver 2 (Port 9001) - Optional
cd client
python driver_client.py --port 9001

# Terminal 6: Driver 3 (Port 9002) - Optional
cd client
python driver_client.py --port 9002
```

### 3. User Clients (Start when you want to request a ride)

Users request rides. Each user runs on a different port:

```bash
# Terminal 7: User 1 (Port 6000)
cd client
python user_client.py --port 6000 --from "123 Main St, Chennai" --to "456 Park Ave, Chennai"

# Terminal 8: User 2 (Port 7000) - Optional
cd client
python user_client.py --port 7000 --from "789 Beach Rd, Chennai" --to "321 Mall St, Chennai"
```

## ⚠️ Important Notes

1. **Servers must be running FIRST** before starting any clients
2. **Driver clients stay running** - they wait for rides continuously
3. **User clients terminate** after receiving a ride assignment (this is by design)
4. **Port conflicts**: Each service needs a unique port
   - Servers: 8000, 8001, 8002 (fixed)
   - Drivers: 9000, 9001, 9002, etc. (you choose)
   - Users: 6000, 7000, etc. (you choose)

## 🔍 Troubleshooting

### Error: "Connection refused on port 6000"
- **Problem**: User client on port 6000 is not running
- **Solution**: Start a user client: `python user_client.py --port 6000`

### Error: "Driver timed out"
- **Problem**: Driver client might be busy or crashed
- **Solution**: Check if driver is running, restart if needed

### Error: "Missing ride or driver info"
- **Problem**: Database issue (should be fixed after migration)
- **Solution**: Make sure you ran `migrate_add_ride_id.py` and `backfill_ride_ids.py`

## 📋 Quick Start Checklist

- [ ] Start `server.py` (Terminal 1)
- [ ] Start `server_matcher.py` (Terminal 2)
- [ ] Start `server_notifier.py` (Terminal 3)
- [ ] Start at least 1 driver: `driver_client.py --port 9000` (Terminal 4)
- [ ] Start a user when you want to test: `user_client.py --port 6000` (Terminal 5)

## 🎯 Typical Workflow

1. **Start all 3 server services** (leave them running)
2. **Start 1-3 driver clients** (leave them running)
3. **Start a user client** when you want to request a ride
4. The system will:
   - User creates ride request
   - Matcher finds available driver
   - Notifier sends assignment to both user and driver
   - Driver auto-accepts and completes ride
   - User client terminates after receiving assignment

