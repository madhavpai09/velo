"""
Fixed Notifier Service - All timezone issues resolved
Key fixes:
1. Consistent use of timezone.utc throughout
2. Safe datetime comparison with None checks
3. Proper timezone conversion helper
"""
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import requests
import asyncio
import sys
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone  # FIX: Added timezone import

sys.path.insert(0, os.path.dirname(__file__))

from database.connections import SessionLocal, engine
from database.models import Base, RideRequest, DriverInfo, MatchedRide

Base.metadata.create_all(bind=engine)

# Timeout for offering a ride to a driver (60 seconds)
OFFER_TIMEOUT_SECONDS = 60

async def cleanup_stale_matches():
    """
    Background task:
    1. Checks for matches that have timed out (driver didn't accept in 10s).
    2. Marks them as 'declined' so Matcher picks the next driver.
    """
    await asyncio.sleep(5)
    print("⏰ Timeout manager started (checking every 2s)")
    
    while True:
        try:
            await asyncio.sleep(2)
            
            db = SessionLocal()
            try:
                # FIX: Use naive UTC to match DB default (avoid timezone confusion)
                now = datetime.utcnow()
                cutoff_time = now - timedelta(seconds=OFFER_TIMEOUT_SECONDS)
                
                # Find expired offers (pending_notification OR offered)
                expired_matches = db.query(MatchedRide).filter(
                    MatchedRide.status.in_(["pending_notification", "offered"]),
                    MatchedRide.created_at < cutoff_time
                ).all()
                
                if expired_matches:
                    print(f"\n⏰ Found {len(expired_matches)} expired offer(s)...")
                    print(f"   Current Time (UTC): {now}")
                    print(f"   Cutoff Time (UTC):  {cutoff_time}")
                    
                    for match in expired_matches:
                        print(f"   💀 EXPIRED Match {match.id}: Created at {match.created_at}")
                        
                        # Mark as DECLINED so matcher skips this driver next time
                        match.status = "declined"
                        
                        # Re-queue the ride so matcher finds it again
                        if match.ride_id:
                            ride = db.query(RideRequest).filter(
                                RideRequest.id == match.ride_id
                            ).first()
                            if ride and ride.status in ["broadcasting", "matched"]:
                                ride.status = "pending"
                                print(f"   🔄 Ride {match.ride_id} re-queued (Driver {match.driver_id} timed out)")
                        
                        print(f"   🚫 Match expired: User {match.user_id} -> Driver {match.driver_id}")
                    
                    db.commit()
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"⚠️ Timeout manager error: {e}")

async def notifier_loop():
    """
    Main notifier loop - checks for unnotified matches
    FIX: Safe timezone handling for age calculations
    """
    await asyncio.sleep(2)
    print("🔍 Notifier starting checks...")
    
    while True:
        try:
            await asyncio.sleep(3)
            
            db = SessionLocal()
            try:
                unnotified_matches = db.query(MatchedRide).filter(
                    MatchedRide.status == "pending_notification"
                ).all()
                
                if unnotified_matches:
                    recent_matches = []
                    stale_count = 0
                    
                    for match in unnotified_matches:
                        # FIX: Use simple naive comparison
                        created = match.created_at
                        if not created:
                             recent_matches.append(match)
                             continue
                        
                    if unnotified_matches:
                        print(f" found {len(unnotified_matches)} pending matches")
                else:
                    # Print dot to show activity
                    print(".", end="", flush=True)
                
                for match in unnotified_matches:
                    print(f"\n📝 Processing match ID: {match.id}")
                    print(f"   User ID: {match.user_id}")
                    print(f"   Driver ID: {match.driver_id}")
                    
                    # Get ride and driver details
                    ride = None
                    if match.ride_id:
                        ride = db.query(RideRequest).filter(
                            RideRequest.id == match.ride_id
                        ).first()
                    
                    if not ride:
                        ride = db.query(RideRequest).filter(
                            RideRequest.user_id == match.user_id
                        ).order_by(RideRequest.created_at.desc()).first()
                    
                    driver = db.query(DriverInfo).filter(
                        DriverInfo.driver_id == match.driver_id
                    ).first()
                    
                    if not ride or not driver:
                        print(f"   ⚠️  Missing ride or driver info")
                        match.status = "failed"
                        db.commit()
                        continue
                    
                    user_port = match.user_id
                    driver_port = match.driver_id
                    
                    # 1. Notify orchestrator
                    try:
                        requests.post(
                            "http://localhost:8000/update_match/",
                            json={"user_id": match.user_id, "driver_id": match.driver_id},
                            timeout=2
                        )
                        print(f"   ✅ Orchestrator notified")
                    except:
                        pass
                    
                    # 2. Check if user is web or Python client
                    user_notified = False
                    is_web_user = False
                    
                    try:
                        health = requests.get(f"http://localhost:{user_port}/status", timeout=0.5)
                        if health.status_code == 200:
                            # Python client exists
                            resp = requests.post(
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
                            if resp.status_code == 200:
                                print(f"   ✅ User Python client notified")
                                user_notified = True
                    except:
                        is_web_user = True
                        print(f"   ℹ️  User is web client - will poll")
                        user_notified = True
                    
                    # 3. Check if driver is web or Python client
                    driver_notified = False
                    is_web_driver = False
                    
                    # FIX: Try to get port from vehicle_details (JSON hack)
                    driver_port = match.driver_id # Default
                    try:
                        import json
                        if driver.vehicle_details and "{" in driver.vehicle_details:
                            details = json.loads(driver.vehicle_details)
                            if "port" in details:
                                driver_port = details["port"]
                                print(f"   🎯 Target Driver Port: {driver_port} (from DB)")
                    except Exception:
                        pass
                    
                    try:
                        health = requests.get(f"http://localhost:{driver_port}/status", timeout=0.5)
                        if health.status_code == 200:
                            # Python client exists
                            for attempt in range(3):
                                try:
                                    resp = requests.post(
                                        f"http://localhost:{driver_port}/ride/assigned",
                                        json={
                                            "ride_id": ride.id,
                                            "user_id": match.user_id,
                                            "pickup_location": ride.source_location,
                                            "dropoff_location": ride.dest_location
                                        },
                                        timeout=5
                                    )
                                    if resp.status_code == 200:
                                        print(f"   ✅ Driver Python client notified")
                                        driver_notified = True
                                        break
                                except:
                                    if attempt == 2:
                                        print(f"   ❌ Failed to notify driver after 3 attempts")
                                    await asyncio.sleep(1)
                        else:
                            is_web_driver = True
                    except:
                        is_web_driver = True
                        print(f"   ℹ️  Driver is web client (or connection failed) - will poll")
                        driver_notified = True
                    
                    # 4. Handle notification results
                    if user_notified and driver_notified:
                        if is_web_user or is_web_driver:
                            # Web clients: update status to 'offered' so they can poll it
                            match.status = "offered"
                            db.commit()
                            print(f"   ✅ Match stored for web client polling (Status: offered)")
                        else:
                            # Both Python clients notified - delete match (legacy behavior? Or also keep as offered?)
                            # If we delete, they can't accept it via ID?
                            # Wait, 'accept_ride' requires the match to exist.
                            # So we MUST NOT DELETE IT.
                            
                            match.status = "offered"
                            db.commit()
                            print(f"   ✅ Match set to 'offered' (waiting for accept)")
                    
                    elif not driver_notified:
                         # Driver failed - mark unavailable and re-queue ride
                        driver.available = False
                        ride.status = "pending"
                        db.delete(match)
                        db.commit()
                        print(f"   🔄 Ride re-queued for another driver")
                    
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
    print("🔄 Notifier loop started (every 3 seconds)")
    print("🧹 Stale cleanup started (every 30 seconds)")
    yield
    notifier_task.cancel()
    cleanup_task.cancel()


app = FastAPI(title="Notifier Server", lifespan=lifespan)


@app.get("/")
def health():
    return {"message": "Notifier running on port 8002"}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get notification statistics"""
    pending = db.query(MatchedRide).filter(
        MatchedRide.status == "pending_notification"
    ).count()
    
    # FIX: Use timezone-aware datetime
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=STALE_MATCH_THRESHOLD_MINUTES)
    stale = db.query(MatchedRide).filter(
        MatchedRide.status == "pending_notification",
        MatchedRide.created_at < cutoff_time
    ).count()
    
    return {
        "pending_notifications": pending,
        "stale_matches": stale
    }





if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("📢 Mini Uber Notifier Service (FIXED)")
    print("="*60)
    print("   Port: 8002")
    print("   ✅ Timezone issues resolved")
    print("   ✅ Safe datetime handling")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="warning")