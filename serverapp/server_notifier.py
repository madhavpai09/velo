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
                    
                    # Get ride details
                    ride = db.query(RideRequest).filter(
                        RideRequest.user_id == match.user_id,
                        RideRequest.status == "matched"
                    ).first()
                    
                    # Get driver details
                    driver = db.query(DriverInfo).filter(
                        DriverInfo.driver_id == match.driver_id
                    ).first()
                    
                    if not ride or not driver:
                        print(f"   ⚠️  Missing ride or driver info")
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
                    
                    # 2. Notify user client
                    try:
                        requests.post(
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
                        print(f"   ✅ User client notified on port {user_port}")
                    except Exception as e:
                        print(f"   ⚠️  Could not notify user client on port {user_port}: {e}")
                    
                    # 3. Notify driver client
                    try:
                        requests.post(
                            f"http://localhost:{driver_port}/ride/assigned",
                            json={
                                "ride_id": ride.id,
                                "user_id": match.user_id,
                                "pickup_location": ride.source_location,
                                "dropoff_location": ride.dest_location
                            },
                            timeout=2
                        )
                        print(f"   ✅ Driver client notified on port {driver_port}")
                    except Exception as e:
                        print(f"   ⚠️  Could not notify driver client on port {driver_port}: {e}")
                    
                    # Delete the match after successful notification
                    db.delete(match)
                    db.commit()
                    print(f"   ✅ Match deleted from database after notification")
                    
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
                "status": m.status
            }
            for m in all_matches
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)