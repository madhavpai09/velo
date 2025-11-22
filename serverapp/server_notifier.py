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

# Stale match threshold
STALE_MATCH_THRESHOLD_MINUTES = 5

def _to_utc(dt):
    """
    FIX: Helper to safely convert any datetime to timezone-aware UTC
    Handles None, naive, and timezone-aware datetimes
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Naive datetime - assume it's UTC
        return dt.replace(tzinfo=timezone.utc)
    # Already timezone-aware - convert to UTC
    return dt.astimezone(timezone.utc)

async def cleanup_stale_matches():
    """
    Background task to clean up stale matches
    FIX: All datetime operations use timezone.utc
    """
    await asyncio.sleep(10)
    
    while True:
        try:
            await asyncio.sleep(30)
            
            db = SessionLocal()
            try:
                # FIX: Use timezone-aware UTC datetime
                cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=STALE_MATCH_THRESHOLD_MINUTES)
                
                stale_matches = db.query(MatchedRide).filter(
                    MatchedRide.status == "pending_notification",
                    MatchedRide.created_at < cutoff_time
                ).all()
                
                if stale_matches:
                    print(f"\n🧹 Found {len(stale_matches)} stale match(es) - cleaning up...")
                    
                    for match in stale_matches:
                        print(f"   🗑️  Deleting stale match: User {match.user_id} ↔ Driver {match.driver_id}")
                        
                        driver = db.query(DriverInfo).filter(
                            DriverInfo.driver_id == match.driver_id
                        ).first()
                        if driver:
                            driver.available = True
                        
                        if match.ride_id:
                            ride = db.query(RideRequest).filter(
                                RideRequest.id == match.ride_id
                            ).first()
                            if ride and ride.status in ["matched", "broadcasting"]:
                                ride.status = "pending"
                                print(f"   🔄 Ride {match.ride_id} re-queued")
                        
                        db.delete(match)
                    
                    db.commit()
                    print(f"   ✅ Cleanup complete")
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"⚠️ Stale match cleanup error: {e}")

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
                    
                    # FIX: Use timezone-aware UTC for current time
                    now = datetime.now(timezone.utc)
                    
                    for match in unnotified_matches:
                        # FIX: Use safe timezone conversion
                        created = _to_utc(match.created_at)
                        if created is None:
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
                            print(f"   ⏰ Skipping {stale_count} stale match(es)")
                    else:
                        print(".", end="", flush=True)
                else:
                    print(".", end="", flush=True)
                
                for match in (recent_matches if unnotified_matches else []):
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
                        print(f"   ℹ️  Driver is web client - will poll")
                        driver_notified = True
                    
                    # 4. Handle notification results
                    if user_notified and driver_notified:
                        if is_web_user or is_web_driver:
                            # Web clients - keep match for polling
                            print(f"   ✅ Match stored for web client polling")
                            db.commit()
                        else:
                            # Both Python clients notified - delete match
                            db.delete(match)
                            db.commit()
                            print(f"   ✅ Match deleted after Python client notification")
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