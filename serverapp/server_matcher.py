from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import asyncio
import requests
import sys
import os
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(__file__))

from database.connections import SessionLocal, engine
from database.models import Base, RideRequest, DriverInfo, MatchedRide

Base.metadata.create_all(bind=engine)

def is_driver_online(driver_id: int) -> bool:
    """Check if driver client is actually online by pinging its health endpoint"""
    try:
        # Driver port is the driver_id itself
        driver_port = driver_id
        response = requests.get(
            f"http://localhost:{driver_port}/status",
            timeout=1  # Quick timeout
        )
        if response.status_code == 200:
            data = response.json()
            # Verify it's the correct driver and available
            return data.get('driver_id') == f"DRIVER-{driver_id}" and data.get('is_available', False)
        return False
    except Exception as e:
        print(f"   ⚠️  Driver {driver_id} is offline: {e}")
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
                online_driver = None
                for driver in available_drivers:
                    print(f"   🔌 Checking driver {driver.driver_id} (port {driver.driver_id})...")
                    if is_driver_online(driver.driver_id):
                        online_driver = driver
                        print(f"   ✅ Driver {driver.driver_id} is ONLINE and available!")
                        break
                    else:
                        # Mark driver as unavailable in database
                        print(f"   ❌ Driver {driver.driver_id} is OFFLINE, marking unavailable")
                        driver.available = False
                        db.commit()
                
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
                ride.status = "matched"
                online_driver.available = False

                # Create matched ride record with status="pending_notification"
                matched = MatchedRide(
                    user_id=ride.user_id,
                    driver_id=online_driver.driver_id,
                    status="pending_notification"
                )
                db.add(matched)
                db.commit()
                
                print(f"   ✅ Match stored in database (ID: {matched.id})")
                    
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
        online = is_driver_online(driver.driver_id)
        results.append({
            "driver_id": driver.driver_id,
            "db_available": driver.available,
            "actually_online": online,
            "port": driver.driver_id
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