from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import asyncio
import requests
import sys
from datetime import datetime
import os
import math
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    filename='matcher.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger(__name__)

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
        
        # FIX: Try to get port from DB object if we have it
        if db is not None:
             driver = db.query(DriverInfo).filter(DriverInfo.driver_id == driver_id).first()
             if driver and driver.vehicle_details and "{" in driver.vehicle_details:
                 try:
                     import json
                     details = json.loads(driver.vehicle_details)
                     if "port" in details:
                         driver_port = details["port"]
                 except:
                     pass

        response = requests.get(
            f"http://localhost:{driver_port}/status",
            timeout=1
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('driver_id') == f"DRIVER-{driver_id}" and data.get('is_available', False)
        return False
    except Exception as e:
        # print(f"   ⚠️  Driver {driver_id} port check failed: {e}")
        return False

def calculate_distance(loc1_str: str, loc2_str: str) -> float:
    """Calculate Haversine distance between two 'lat,lng' strings"""
    try:
        lat1, lng1 = map(float, loc1_str.split(','))
        lat2, lng2 = map(float, loc2_str.split(','))
        
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dlng/2) * math.sin(dlng/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    except:
        return float('inf')

# Background task to check for matches every 5 seconds
async def matcher_loop():
    """Background task that wakes every 5s and matches rides"""
    while True:
        try:
            await asyncio.sleep(5)
            logger.info("🔍 Auto-checking for pending rides...")
            print("🔍 Auto-checking for pending rides...")
            
            # Get database session
            db = SessionLocal()
            try:
                # Find pending rides - PRIORITIZE school_pool
                # Fetch ALL pending rides to prevent blocking
                school_rides = db.query(RideRequest).filter(
                    RideRequest.status == "pending",
                    RideRequest.ride_type == "school_pool"
                ).all()
                
                normal_rides = db.query(RideRequest).filter(
                    RideRequest.status == "pending",
                    RideRequest.ride_type != "school_pool" # Avoid duplicates if we just did != school_pool
                ).all()
                
                # Logic to avoid picking up school pool twice if simple query used
                # Actually, simplest is fetch all pending and sort/filter in python or just concat
                # But filter(...) is safer.
                # Let's just fetch ALL pending and sort.
                
                all_pending = db.query(RideRequest).filter(RideRequest.status == "pending").all()
                
                if not all_pending:
                    print("   ℹ️  No pending rides")
                    continue
                
                # Sort: School pool first, then by ID (FIFO)
                all_pending.sort(key=lambda r: (r.ride_type != "school_pool", r.id))
                
                print(f"   📋 Processing {len(all_pending)} pending ride(s)...")
                
                for ride in all_pending:
                    logger.info(f"   📍 Processing pending ride {ride.id} from user {ride.user_id}")
                    # print(f"   📍 Processing pending ride {ride.id} from user {ride.user_id}")
                    
                    # 1. Get Available Drivers (Fresh Query)
                    available_drivers = db.query(DriverInfo).filter(
                        DriverInfo.available == True
                    ).all()
                    
                    # 2. Filter out drivers who ALREADY have a pending/offered match
                    # (To prevent double-booking a driver who hasn't accepted yet)
                    active_matches = db.query(MatchedRide.driver_id).filter(
                        MatchedRide.status.in_(["pending_notification", "offered"])
                    ).all()
                    busy_driver_ids = {m[0] for m in active_matches}
                    
                    available_drivers = [d for d in available_drivers if d.driver_id not in busy_driver_ids]
                    
                    if not available_drivers:
                        logger.info("   ℹ️  No available (free) drivers in database")
                        # print("   ℹ️  No available (free) drivers in database")
                        continue

                    # NEW: Filter for Safe Drivers if School Priority
                    if ride.ride_type == "school_priority":
                        available_drivers = [d for d in available_drivers if d.is_verified_safe]
                        if not available_drivers:
                            print("   ⚠️  No SAFE drivers available for school ride")
                            continue
                    
                    # Get declined drivers for THIS ride
                    declined_matches = db.query(MatchedRide).filter(
                        MatchedRide.ride_id == ride.id,
                        MatchedRide.status == "declined"
                    ).all()
                    declined_driver_ids = {m.driver_id for m in declined_matches}
                    
                    # Filter out declined drivers
                    candidates = [d for d in available_drivers if d.driver_id not in declined_driver_ids]
                    
                    if not candidates:
                        # Log only if this is the only ride, otherwise it's spammy
                        if len(all_pending) == 1:
                            print(f"   ℹ️  All available drivers have declined ride {ride.id}")
                        continue

                    print(f"   👥 Ride {ride.id}: Found {len(candidates)} candidate(s) (excluding {len(declined_driver_ids)} declined)")
                    
                    # Calculate distances and sort
                    driver_distances = []
                    for driver in candidates:
                        dist = calculate_distance(ride.source_location, driver.current_location)
                        driver_distances.append((driver, dist))
                    
                    driver_distances.sort(key=lambda x: x[1])
                    
                    # Check drivers in order of proximity
                    online_driver = None
                    for driver, dist in driver_distances:
                        # print(f"   🔌 Checking driver {driver.driver_id} ({dist:.2f} km away)...")
                        if is_driver_online(driver.driver_id, db=db):
                            online_driver = driver
                            print(f"   ✅ Ride {ride.id}: Match found! Driver {driver.driver_id} ({dist:.2f} km away)")
                            break
                        else:
                            # Driver not found via port check OR heartbeat is stale
                            # print(f"   ❌ Driver {driver.driver_id} is OFFLINE")
                            continue
                    
                    if not online_driver:
                        # print(f"   ℹ️  Ride {ride.id}: No ONLINE drivers found among candidates")
                        continue
                    
                    # Found a match!
                    # Update status
                    ride.status = "broadcasting"
                    
                    # Create match
                    new_match = MatchedRide(
                        user_id=ride.user_id,
                        driver_id=online_driver.driver_id,
                        ride_id=ride.id,
                        status="pending_notification",
                        created_at=datetime.utcnow()
                    )
                    db.add(new_match)
                    db.commit()
                    db.refresh(new_match)
                    
                    print(f"   🚀 Match Created: Ride {ride.id} -> Driver {online_driver.driver_id} (ID: {new_match.id})")
                    
                    # Since we matched this ride, we should probably stop processing this ride
                    # And maybe move to next? Yes.
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"   ⚠️  Matcher loop error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            print(f"   ⚠️  Matcher loop error: {e}")
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