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

# Background task to check for unnotified matches every 3 seconds
async def notifier_loop():
    """Background task that checks matched_rides table and notifies clients"""
    await asyncio.sleep(2)  # Initial delay to let other services start
    print("🔍 Notifier starting checks...")
    
    while True:
        try:
            await asyncio.sleep(3)
            
            # Get database session
            db = SessionLocal()
            try:
                # Find matches that haven't been notified (status = "pending_notification")
                # Don't process matches that are already accepted/completed
                unnotified_matches = db.query(MatchedRide).filter(
                    MatchedRide.status == "pending_notification"
                ).all()
                
                if unnotified_matches:
                    print(f"\n📢 Found {len(unnotified_matches)} unnotified match(es)")
                else:
                    print(".", end="", flush=True)  # Show heartbeat
                
                for match in unnotified_matches:
                    print(f"\n📝 Processing match ID: {match.id}")
                    print(f"   User ID: {match.user_id}")
                    print(f"   Driver ID: {match.driver_id}")
                    print(f"   Ride ID: {match.ride_id}")
                    
                    # Get ride details - prefer ride_id if available, otherwise fallback to user_id query
                    ride = None
                    if match.ride_id:
                        ride = db.query(RideRequest).filter(
                            RideRequest.id == match.ride_id
                        ).first()
                    
                    # Fallback: if ride_id not available or ride not found, try user_id query
                    if not ride:
                        ride = db.query(RideRequest).filter(
                            RideRequest.user_id == match.user_id
                        ).order_by(RideRequest.created_at.desc()).first()
                    
                    # Get driver details
                    driver = db.query(DriverInfo).filter(
                        DriverInfo.driver_id == match.driver_id
                    ).first()
                    
                    if not ride or not driver:
                        print(f"   ⚠️  Missing ride or driver info")
                        if not ride:
                            print(f"      Ride not found (ride_id: {match.ride_id}, user_id: {match.user_id})")
                        if not driver:
                            print(f"      Driver not found (driver_id: {match.driver_id})")
                        
                        # Mark match as failed to prevent infinite retries
                        match.status = "failed"
                        db.commit()
                        print(f"   ❌ Marked match {match.id} as failed - will not retry")
                        continue
                    
                    # FIXED: Port mapping logic
                    # User port is the user_id itself (since user_id defaults to port in user_client.py)
                    user_port = match.user_id
                    
                    # Driver port is the driver_id itself (since it's extracted from port in driver_client.py)
                    driver_port = match.driver_id
                    
                    print(f"   🔌 User port: {user_port}, Driver port: {driver_port}")
                    
                    # Prepare notification data
                    match_data = {
                        "user_id": match.user_id,
                        "driver_id": match.driver_id,
                        "ride_id": ride.id,
                        "source_location": ride.source_location,
                        "dest_location": ride.dest_location,
                        "driver_location": driver.current_location
                    }
                    
                    # 1. Notify orchestrator
                    try:
                        requests.post(
                            "http://localhost:8000/update_match/",
                            json={
                                "user_id": match.user_id,
                                "driver_id": match.driver_id
                            },
                            timeout=2
                        )
                        print(f"   ✅ Orchestrator notified")
                    except Exception as e:
                        print(f"   ⚠️  Could not notify orchestrator: {e}")
                    
                    # 2. Notify user client (check if web user or Python client)
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
                                print(f"   ⚠️  Could not notify user client on port {user_port}: {e}")
                    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                        # Port doesn't exist - this is a web user
                        is_web_user = True
                        print(f"   ℹ️  User {match.user_id} is a web user (no port) - will poll for assignment")
                    
                    # For web users, we keep the match in database and let them poll
                    if is_web_user:
                        user_notified = True  # Consider it "notified" since it's in DB for polling
                    
                    # 3. Notify driver client (with retry and health check)
                    # For web drivers, we'll let them poll for assignments
                    # For Python clients, try to notify via port
                    driver_notified = False
                    is_web_driver = False
                    
                    # First check if driver has a port (Python client) or is web driver
                    try:
                        health_check = requests.get(
                            f"http://localhost:{driver_port}/status",
                            timeout=0.5  # Quick check
                        )
                        if health_check.status_code == 200:
                            # Python client - try to notify
                            for attempt in range(3):
                                try:
                                    response = requests.post(
                                        f"http://localhost:{driver_port}/ride/assigned",
                                        json={
                                            "ride_id": ride.id,
                                            "user_id": match.user_id,
                                            "pickup_location": ride.source_location,
                                            "dropoff_location": ride.dest_location
                                        },
                                        timeout=5
                                    )
                                    
                                    if response.status_code == 200:
                                        print(f"   ✅ Driver client notified on port {driver_port}")
                                        driver_notified = True
                                        break
                                except Exception as e:
                                    if attempt == 2:
                                        print(f"   ⚠️  Could not notify Python driver on port {driver_port}: {e}")
                                    await asyncio.sleep(1)
                        else:
                            is_web_driver = True
                    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                        # Port doesn't exist - this is a web driver
                        is_web_driver = True
                        print(f"   ℹ️  Driver {match.driver_id} is a web driver (no port) - will poll for assignment")
                    
                    # For web drivers, we keep the match in database and let them poll
                    if is_web_driver:
                        print(f"   ✅ Match stored - web driver {match.driver_id} can poll for assignment")
                        driver_notified = True  # Consider it "notified" since it's in DB for polling
                    
                    # Check if both user and driver are notified (or web clients)
                    if user_notified and driver_notified:
                        # Both notified - keep match in DB for web clients to poll, or delete for Python clients
                        if is_web_user or is_web_driver:
                            # Web client(s) - keep match in DB for polling
                            print(f"   ✅ Match stored - web client(s) can poll for assignment")
                            db.commit()
                            continue  # Skip deletion, let clients poll for it
                        else:
                            # Both Python clients - delete match after notification
                            db.delete(match)
                            db.commit()
                            print(f"   ✅ Match deleted from database after notification")
                    elif not driver_notified:
                        print(f"   ❌ FAILED to notify driver {driver_port} after 3 attempts")
                        print(f"   📌 Marking driver {match.driver_id} as unavailable in database")
                        
                        # Mark driver as unavailable
                        driver.available = False
                        
                        # Re-queue the ride by changing status back to pending
                        ride.status = "pending"
                        
                        # Delete the failed match
                        db.delete(match)
                        db.commit()
                        print(f"   🔄 Ride {ride.id} re-queued for another driver")
                        continue
                    elif not user_notified:
                        print(f"   ❌ FAILED to notify user {user_port}")
                        # Keep match in DB - user might come online later (for web users)
                        # Or delete if it's been too long (could add timeout logic later)
                        db.commit()
                        continue
                    
            finally:
                db.close()
                
        except Exception as e:
            print(f"\n⚠️  Notifier loop error: {e}")
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
    
    return {
        "pending_notifications": pending,
        "note": "Matches are deleted after successful notification"
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
    print("📢 Mini Uber Notifier Service")
    print("="*60)
    print("   Port: 8002")
    print("   Checking for matches every 3 seconds")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="warning")