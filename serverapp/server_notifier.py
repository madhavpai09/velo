from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import requests
import asyncio
import sys
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))

from database.connections import SessionLocal, engine
from database.models import Base, RideRequest, DriverInfo, MatchedRide

Base.metadata.create_all(bind=engine)

# Stale match threshold - matches older than this are considered stale
STALE_MATCH_THRESHOLD_MINUTES = 5

async def cleanup_stale_matches():
    """Background task to clean up stale matches that are too old"""
    await asyncio.sleep(10)  # Wait 10 seconds before first cleanup
    
    while True:
        try:
            await asyncio.sleep(30)  # Run every 30 seconds
            
            db = SessionLocal()
            try:
                # Use timezone-aware UTC now and compare against stored timestamps (normalize below)
                cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=STALE_MATCH_THRESHOLD_MINUTES)
                
                # Find old matches that haven't been processed
                stale_matches = db.query(MatchedRide).filter(
                    MatchedRide.status == "pending_notification",
                    MatchedRide.created_at < cutoff_time
                ).all()
                
                if stale_matches:
                    print(f"\n🧹 Found {len(stale_matches)} stale match(es) - cleaning up...")
                    
                    for match in stale_matches:
                        print(f"   🗑️  Deleting stale match: User {match.user_id} ↔ Driver {match.driver_id}")
                        
                        # Mark driver as available again
                        driver = db.query(DriverInfo).filter(
                            DriverInfo.driver_id == match.driver_id
                        ).first()
                        if driver:
                            driver.available = True
                        
                        # Re-queue the ride if it's still pending/matched
                        if match.ride_id:
                            ride = db.query(RideRequest).filter(
                                RideRequest.id == match.ride_id
                            ).first()
                            if ride and ride.status in ["matched", "broadcasting"]:
                                ride.status = "pending"
                                print(f"   🔄 Ride {match.ride_id} re-queued")
                        
                        # Delete the stale match
                        db.delete(match)
                    
                    db.commit()
                    print(f"   ✅ Cleanup complete")
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"⚠️ Stale match cleanup error: {e}")

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
                    # Check if matches are recent (not stale from old sessions)
                    recent_matches = []
                    stale_count = 0
                    
                    # Helper to safely compute age against possibly timezone-aware or naive DB timestamps
                    def _to_utc(dt):
                        if dt is None:
                            return None
                        if dt.tzinfo is None:
                            return dt.replace(tzinfo=timezone.utc)
                        return dt.astimezone(timezone.utc)

                    now = datetime.now(timezone.utc)
                    for match in unnotified_matches:
                        created = _to_utc(match.created_at)
                        if created is None:
                            # If no timestamp, treat as recent
                            recent_matches.append(match)
                            continue
                        age_minutes = (now - created).total_seconds() / 60
                        if age_minutes < STALE_MATCH_THRESHOLD_MINUTES:
                            recent_matches.append(match)
                        else:
                            stale_count += 1
                    
                    if recent_matches:
                        print(f"\n📢 Found {len(recent_matches)} recent unnotified match(es)")
                        if stale_count > 0:
                            print(f"   ⏰ Skipping {stale_count} stale match(es) (will be cleaned up)")
                    else:
                        print(".", end="", flush=True)  # Show heartbeat
                else:
                    print(".", end="", flush=True)  # Show heartbeat
                
                for match in recent_matches if unnotified_matches else []:
                    print(f"\n📝 Processing match ID: {match.id}")
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
                    
                    # Port mapping
                    user_port = match.user_id
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
                    
                    # 2. Notify user client
                    user_notified = False
                    is_web_user = False
                    
                    try:
                        health_check = requests.get(
                            f"http://localhost:{user_port}/status",
                            timeout=0.5
                        )
                        if health_check.status_code == 200:
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
                        is_web_user = True
                        print(f"   ℹ️  User {match.user_id} is a web user (no port) - will poll for assignment")
                    
                    if is_web_user:
                        user_notified = True
                    
                    # 3. Notify driver client
                    driver_notified = False
                    is_web_driver = False
                    
                    try:
                        health_check = requests.get(
                            f"http://localhost:{driver_port}/status",
                            timeout=0.5
                        )
                        if health_check.status_code == 200:
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
                        is_web_driver = True
                        print(f"   ℹ️  Driver {match.driver_id} is a web driver (no port) - will poll for assignment")
                    
                    if is_web_driver:
                        print(f"   ✅ Match stored - web driver {match.driver_id} can poll for assignment")
                        driver_notified = True
                    
                    # Check if both notified
                    if user_notified and driver_notified:
                        if is_web_user or is_web_driver:
                            print(f"   ✅ Match stored - web client(s) can poll for assignment")
                            db.commit()
                            continue
                        else:
                            db.delete(match)
                            db.commit()
                            print(f"   ✅ Match deleted from database after notification")
                    elif not driver_notified:
                        print(f"   ❌ FAILED to notify driver {driver_port} after 3 attempts")
                        print(f"   📌 Marking driver {match.driver_id} as unavailable in database")
                        
                        driver.available = False
                        ride.status = "pending"
                        db.delete(match)
                        db.commit()
                        print(f"   🔄 Ride {ride.id} re-queued for another driver")
                        continue
                    elif not user_notified:
                        print(f"   ❌ FAILED to notify user {user_port}")
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
    notifier_task = asyncio.create_task(notifier_loop())
    cleanup_task = asyncio.create_task(cleanup_stale_matches())
    print("🔄 Notifier loop started (checking every 3 seconds).")
    print("🧹 Stale match cleanup started (checking every 30 seconds).")
    yield
    notifier_task.cancel()
    cleanup_task.cancel()
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
    
    # Count stale matches
    cutoff_time = datetime.utcnow() - timedelta(minutes=STALE_MATCH_THRESHOLD_MINUTES)
    stale = db.query(MatchedRide).filter(
        MatchedRide.status == "pending_notification",
        MatchedRide.created_at < cutoff_time
    ).count()
    
    return {
        "pending_notifications": pending,
        "stale_matches": stale,
        "note": "Matches older than 5 minutes are considered stale and will be cleaned up"
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
                "status": m.status,
                "created_at": m.created_at.isoformat(),
                "age_minutes": (datetime.utcnow() - m.created_at).total_seconds() / 60
            }
            for m in all_matches
        ]
    }


@app.post("/cleanup/stale-matches")
def manual_cleanup(db: Session = Depends(get_db)):
    """Manual endpoint to clean up stale matches"""
    cutoff_time = datetime.utcnow() - timedelta(minutes=STALE_MATCH_THRESHOLD_MINUTES)
    
    stale_matches = db.query(MatchedRide).filter(
        MatchedRide.status == "pending_notification",
        MatchedRide.created_at < cutoff_time
    ).all()
    
    count = len(stale_matches)
    
    for match in stale_matches:
        # Mark driver as available
        driver = db.query(DriverInfo).filter(
            DriverInfo.driver_id == match.driver_id
        ).first()
        if driver:
            driver.available = True
        
        # Re-queue ride
        if match.ride_id:
            ride = db.query(RideRequest).filter(
                RideRequest.id == match.ride_id
            ).first()
            if ride and ride.status in ["matched", "broadcasting"]:
                ride.status = "pending"
        
        db.delete(match)
    
    db.commit()
    
    return {
        "message": f"Cleaned up {count} stale match(es)",
        "cleaned": count
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
    print("   Auto-cleanup of stale matches (>5 minutes old)")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="warning")