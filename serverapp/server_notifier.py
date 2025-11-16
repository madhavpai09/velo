from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import requests
import asyncio
import sys
import os
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(__file__))

from database.connections import SessionLocal, engine
from database.models import Base, RideRequest, DriverInfo, MatchedRide

Base.metadata.create_all(bind=engine)

# Background task to check for accepted rides and notify users
async def notifier_loop():
    """Background task that checks for accepted rides and notifies users"""
    await asyncio.sleep(2)  # Initial delay to let other services start
    print("🔔 Notifier starting checks...")
    
    while True:
        try:
            await asyncio.sleep(3)
            
            # Get database session
            db = SessionLocal()
            try:
                # Find matches where driver has accepted (status = "accepted")
                # These are rides that need user notification
                accepted_matches = db.query(MatchedRide).filter(
                    MatchedRide.status == "accepted"
                ).all()
                
                if accepted_matches:
                    print(f"\n🔔 Found {len(accepted_matches)} accepted ride(s) to notify users")
                else:
                    print(".", end="", flush=True)  # Show heartbeat
                
                for match in accepted_matches:
                    print(f"\n📢 Processing accepted ride ID: {match.id}")
                    print(f"   User ID: {match.user_id}")
                    print(f"   Driver ID: {match.driver_id}")
                    print(f"   Ride ID: {match.ride_id}")
                    
                    # Get ride details
                    ride = None
                    if match.ride_id:
                        ride = db.query(RideRequest).filter(
                            RideRequest.id == match.ride_id
                        ).first()
                    
                    if not ride:
                        ride = db.query(RideRequest).filter(
                            RideRequest.user_id == match.user_id
                        ).order_by(RideRequest.created_at.desc()).first()
                    
                    # Get driver details
                    driver = db.query(DriverInfo).filter(
                        DriverInfo.driver_id == match.driver_id
                    ).first()
                    
                    if not ride or not driver:
                        print(f"   ⚠️ Missing ride or driver info")
                        if not ride:
                            print(f"      Ride not found (ride_id: {match.ride_id}, user_id: {match.user_id})")
                        if not driver:
                            print(f"      Driver not found (driver_id: {match.driver_id})")
                        
                        # Mark match as failed
                        match.status = "failed"
                        db.commit()
                        print(f"   ❌ Marked match {match.id} as failed - will not retry")
                        continue
                    
                    # Port mapping
                    user_port = match.user_id
                    driver_port = match.driver_id
                    
                    print(f"   🔌 User port: {user_port}, Driver port: {driver_port}")
                    
                    # Notify user client (check if web user or Python client)
                    user_notified = False
                    is_web_user = False
                    
                    try:
                        # Try to check if user has a port (Python client)
                        health_check = requests.get(
                            f"http://localhost:{user_port}/status",
                            timeout=0.5
                        )
                        if health_check.status_code == 200:
                            # Python client - try to notify
                            try:
                                response = requests.post(
                                    f"http://localhost:{user_port}/ride/assigned",
                                    json={
                                        "ride_id": ride.id,
                                        "driver_id": match.driver_id,
                                        "driver_name": f"Driver {match.driver_id}",
                                        "driver_location": driver.current_location,
                                        "pickup_location": ride.source_location,
                                        "dropoff_location": ride.dest_location
                                    },
                                    timeout=2
                                )
                                if response.status_code == 200:
                                    print(f"   ✅ User client notified on port {user_port}")
                                    user_notified = True
                            except Exception as e:
                                print(f"   ⚠️ Could not notify user client on port {user_port}: {e}")
                    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                        # Port doesn't exist - this is a web user
                        is_web_user = True
                        print(f"   ℹ️ User {match.user_id} is a web user (no port) - polling will show status")
                        user_notified = True  # Web users poll for status
                    
                    if user_notified:
                        # Update match status to "user_notified" so we don't process it again
                        match.status = "user_notified"
                        db.commit()
                        print(f"   ✅ Match {match.id} marked as user_notified")
                    else:
                        print(f"   ⚠️ Could not notify user {user_port}")
                    
            finally:
                db.close()
                
        except Exception as e:
            print(f"\n⚠️ Notifier loop error: {e}")
            import traceback
            traceback.print_exc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(notifier_loop())
    print("🔄 Notifier loop started (checking every 3 seconds).")
    yield
    task.cancel()
    print("🛑 Notifier loop stopped.")


app = FastAPI(title="Notifier Server", lifespan=lifespan)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def health():
    return {"message": "Notifier running on port 8002"}


@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get notification statistics"""
    pending = db.query(MatchedRide).filter(MatchedRide.status == "pending_notification").count()
    accepted = db.query(MatchedRide).filter(MatchedRide.status == "accepted").count()
    notified = db.query(MatchedRide).filter(MatchedRide.status == "user_notified").count()
    
    return {
        "pending_driver_acceptance": pending,
        "accepted_awaiting_user_notification": accepted,
        "user_notified": notified
    }


@app.get("/debug/matches")
def debug_matches(db: Session = Depends(get_db)):
    """Debug endpoint to see all matches in database"""
    all_matches = db.query(MatchedRide).all()
    return {
        "count": len(all_matches),
        "matches": [
            {
                "id": m.id,
                "user_id": m.user_id,
                "driver_id": m.driver_id,
                "ride_id": m.ride_id,
                "status": m.status
            }
            for m in all_matches
        ]
    }


@app.get("/debug/active-clients")
def check_active_clients(db: Session = Depends(get_db)):
    """Check which clients (users and drivers) are actually running"""
    results = {
        "drivers": [],
        "users": []
    }
    
    # Check drivers
    drivers = db.query(DriverInfo).all()
    for driver in drivers:
        port = driver.driver_id
        try:
            resp = requests.get(f"http://localhost:{port}/status", timeout=1)
            results["drivers"].append({
                "driver_id": driver.driver_id,
                "port": port,
                "online": True,
                "available": resp.json().get("is_available", False)
            })
        except:
            results["drivers"].append({
                "driver_id": driver.driver_id,
                "port": port,
                "online": False,
                "available": False
            })
    
    # Check users from recent rides
    rides = db.query(RideRequest).limit(10).all()
    checked_users = set()
    for ride in rides:
        if ride.user_id not in checked_users:
            checked_users.add(ride.user_id)
            port = ride.user_id
            try:
                resp = requests.get(f"http://localhost:{port}/status", timeout=1)
                results["users"].append({
                    "user_id": ride.user_id,
                    "port": port,
                    "online": True
                })
            except:
                results["users"].append({
                    "user_id": ride.user_id,
                    "port": port,
                    "online": False
                })
    
    return results


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🔔 Mini Uber Notifier Service")
    print("="*60)
    print("   Port: 8002")
    print("   Checking for accepted rides every 3 seconds")
    print("   Users notified ONLY after driver accepts")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="warning")