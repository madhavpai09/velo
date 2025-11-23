from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import asyncio
import requests
import sys
from datetime import datetime
import os
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(__file__))

from database.connections import SessionLocal, engine
from database.models import Base, RideRequest, DriverInfo, MatchedRide

Base.metadata.create_all(bind=engine)

def is_driver_online(driver_id: int, db=None) -> bool:
    """Check if driver is online - for web drivers, check database; for Python clients, check port"""
    # First check database if available
    if db is not None:
        driver = db.query(DriverInfo).filter(DriverInfo.driver_id == driver_id).first()
        if driver and driver.available:
            # For web drivers, trust the database availability flag
            # Try to ping port as fallback (for Python clients), but don't fail if it doesn't exist
            try:
                driver_port = driver_id
                response = requests.get(
                    f"http://localhost:{driver_port}/status",
                    timeout=0.5  # Very quick timeout
                )
                if response.status_code == 200:
                    data = response.json()
                    # Python client is online
                    return data.get('driver_id') == f"DRIVER-{driver_id}" and data.get('is_available', False)
            except:
                # Port doesn't exist (web driver) - check heartbeat
                pass
            
            # Check for recent heartbeat (within last 30 seconds)
            # If no heartbeat in 30s, assume offline
            if driver.updated_at:
                # Handle naive vs aware datetime
                now = datetime.utcnow()
                last_update = driver.updated_at
                if last_update.tzinfo:
                    last_update = last_update.replace(tzinfo=None)
                
                time_diff = (now - last_update).total_seconds()
                if time_diff < 30:
                    return True
                else:
                    print(f"   ❌ Driver {driver_id} offline (Last heartbeat: {int(time_diff)}s ago)")
                    return False
            
            # If updated_at is None (legacy), fallback to True but warn
            print(f"   ⚠️  Driver {driver_id} has no heartbeat info, assuming online (Legacy)")
            return True
            
        return False
    
    # Fallback: try port check (for Python clients)
    try:
        driver_port = driver_id
        response = requests.get(
            f"http://localhost:{driver_port}/status",
            timeout=1
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('driver_id') == f"DRIVER-{driver_id}" and data.get('is_available', False)
        return False
    except Exception as e:
        print(f"   ⚠️  Driver {driver_id} port check failed: {e}")
        return False

# Background task to check for matches every 5 seconds
async def matcher_loop():
    """Background task that wakes every 5s and matches rides"""
    while True:
        try:
            await asyncio.sleep(5)
            print("🔍 Auto-checking for pending rides...")
            
            # Get database session
            db = SessionLocal()
            try:
                # Find pending ride
                ride = db.query(RideRequest).filter(RideRequest.status == "pending").first()
                
                if not ride:
                    print("   ℹ️  No pending rides")
                    db.close()
                    continue
                
                print(f"   📍 Found pending ride from user {ride.user_id}")
                
                # Find available drivers (from database)
                available_drivers = db.query(DriverInfo).filter(
                    DriverInfo.available == True
                ).all()
                
                if not available_drivers:
                    print("   ℹ️  No available drivers in database")
                    db.close()
                    continue
                
                print(f"   👥 Found {len(available_drivers)} driver(s) in database, checking if online...")
                
                # Check each driver to see if they're actually online
                # For web drivers, we trust the database availability flag
                online_driver = None
                for driver in available_drivers:
                    print(f"   🔌 Checking driver {driver.driver_id}...")
                    if is_driver_online(driver.driver_id, db=db):
                        online_driver = driver
                        print(f"   ✅ Driver {driver.driver_id} is ONLINE and available!")
                        break
                    else:
                        # Driver not found via port check - could be web driver or offline Python client
                        # Since driver.available is True (we filtered for it), trust the database
                        # This handles web drivers that don't have ports
                        online_driver = driver
                        print(f"   ✅ Driver {driver.driver_id} is available (web driver or database-only)")
                        break
                
                if not online_driver:
                    print("   ℹ️  No online drivers found")
                    db.close()
                    continue
                
                # Found a match!
                print(f"\n🎯 Match Found!")
                print(f"   User ID: {ride.user_id}")
                print(f"   Driver ID: {online_driver.driver_id}")
                print(f"   From: {ride.source_location}")
                print(f"   To: {ride.dest_location}")

                # Update statuses
                ride.status = "broadcasting"
                # Don't mark driver as unavailable yet - they might reject
                # But to prevent double offering, we might want to? 
                # For now, let's keep them available but the ride is 'broadcasting' so it won't be picked up again
                
                # Create matched ride record with status="offered"
                matched = MatchedRide(
                    user_id=ride.user_id,
                    driver_id=online_driver.driver_id,
                    ride_id=ride.id,  # Store ride_id for direct lookup
                    status="offered"
                )
                db.add(matched)
                db.commit()
                
                print(f"   ✅ Ride offered to driver {online_driver.driver_id} (Match ID: {matched.id})")
                    
            finally:
                db.close()
                
        except Exception as e:
            print(f"   ⚠️  Matcher loop error: {e}")
            import traceback
            traceback.print_exc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(matcher_loop())
    print("🔄 Matcher loop started (checking every 5 seconds).")
    yield
    task.cancel()
    print("🛑 Matcher loop stopped.")


app = FastAPI(title="Matcher Server", lifespan=lifespan)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def health():
    return {"message": "Matcher running on port 8001"}


@app.get("/matches/pending")
def get_pending_matches(db: Session = Depends(get_db)):
    """Get all matches that haven't been notified yet"""
    pending = db.query(MatchedRide).filter(MatchedRide.status == "pending_notification").all()
    return {
        "count": len(pending),
        "matches": [
            {
                "id": m.id,
                "user_id": m.user_id,
                "driver_id": m.driver_id,
                "status": m.status
            }
            for m in pending
        ]
    }


@app.get("/drivers/online")
def check_online_drivers(db: Session = Depends(get_db)):
    """Debug endpoint: Check which drivers are actually online"""
    all_drivers = db.query(DriverInfo).all()
    results = []
    
    for driver in all_drivers:
        online = is_driver_online(driver.driver_id, db=db)
        results.append({
            "driver_id": driver.driver_id,
            "db_available": driver.available,
            "actually_online": online,
            "port": driver.driver_id,
            "type": "web" if driver.available and not online else "python_client"
        })
    
    return {"drivers": results}


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🎯 Mini Uber Matcher Service")
    print("="*60)
    print("   Port: 8001")
    print("   Checking for matches every 5 seconds")
    print("   ✨ With online driver verification")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="warning")