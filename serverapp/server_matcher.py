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

def is_driver_online(driver_id: int, db=None) -> bool:
    """Check if driver is online"""
    if db is not None:
        driver = db.query(DriverInfo).filter(DriverInfo.driver_id == driver_id).first()
        if driver and driver.available:
            try:
                driver_port = driver_id
                response = requests.get(
                    f"http://localhost:{driver_port}/status",
                    timeout=0.5
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get('driver_id') == f"DRIVER-{driver_id}" and data.get('is_available', False)
            except:
                pass
            return True
        return False
    
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
        return False

# Background task to check for matches every 5 seconds
async def matcher_loop():
    """Background task that broadcasts ride requests to multiple nearby drivers"""
    while True:
        try:
            await asyncio.sleep(5)
            print("🔍 Auto-checking for pending rides...")
            
            db = SessionLocal()
            try:
                # Find pending ride
                ride = db.query(RideRequest).filter(RideRequest.status == "pending").first()
                
                if not ride:
                    print("   ℹ️ No pending rides")
                    db.close()
                    continue
                
                print(f"   🚗 Found pending ride from user {ride.user_id}")
                
                # Find ALL available drivers (not just one)
                available_drivers = db.query(DriverInfo).filter(
                    DriverInfo.available == True
                ).all()
                
                if not available_drivers:
                    print("   ℹ️ No available drivers in database")
                    db.close()
                    continue
                
                print(f"   👥 Found {len(available_drivers)} available driver(s)")
                
                # Filter to only online drivers
                online_drivers = []
                for driver in available_drivers:
                    if is_driver_online(driver.driver_id, db=db):
                        online_drivers.append(driver)
                        print(f"   ✅ Driver {driver.driver_id} is online")
                
                if not online_drivers:
                    print("   ℹ️ No online drivers found")
                    db.close()
                    continue
                
                # BROADCAST: Create ride offers for ALL online drivers
                print(f"\n📢 Broadcasting ride to {len(online_drivers)} driver(s)!")
                print(f"   User ID: {ride.user_id}")
                print(f"   From: {ride.source_location}")
                print(f"   To: {ride.dest_location}")
                
                # Update ride status to "broadcasting"
                ride.status = "broadcasting"
                
                # Create matched ride records for all online drivers with status "broadcast"
                for driver in online_drivers:
                    # Check if this driver already has a broadcast for this ride
                    existing = db.query(MatchedRide).filter(
                        MatchedRide.ride_id == ride.id,
                        MatchedRide.driver_id == driver.driver_id
                    ).first()
                    
                    if not existing:
                        matched = MatchedRide(
                            user_id=ride.user_id,
                            driver_id=driver.driver_id,
                            ride_id=ride.id,
                            status="broadcast"  # New status for broadcast offers
                        )
                        db.add(matched)
                        print(f"   📤 Broadcast created for driver {driver.driver_id}")
                
                db.commit()
                print(f"   ✅ Ride broadcast to {len(online_drivers)} driver(s)")
                print(f"   ⏳ Waiting for first driver to accept...")
                    
            finally:
                db.close()
                
        except Exception as e:
            print(f"   ⚠️ Matcher loop error: {e}")
            import traceback
            traceback.print_exc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(matcher_loop())
    print("🔄 Matcher loop started (broadcasting to multiple drivers).")
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
    pending = db.query(MatchedRide).filter(
        MatchedRide.status.in_(["pending_notification", "broadcast"])
    ).all()
    return {
        "count": len(pending),
        "matches": [
            {
                "id": m.id,
                "user_id": m.user_id,
                "driver_id": m.driver_id,
                "ride_id": m.ride_id,
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
    print("   Broadcasting to multiple nearby drivers")
    print("   First to accept wins!")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="warning")