from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import asyncio
import sys
import os
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(__file__))

from database.connections import SessionLocal, engine
from database.models import Base, RideRequest, DriverInfo, MatchedRide

Base.metadata.create_all(bind=engine)

# Background task to check for matches every 5 seconds
async def matcher_loop():
    """Background task that wakes every 5s and matches rides"""
    while True:
        try:
            await asyncio.sleep(5)
            print("🔁 Auto-checking for pending rides...")
            
            # Get database session
            db = SessionLocal()
            try:
                # Find pending ride and available driver
                ride = db.query(RideRequest).filter(RideRequest.status == "pending").first()
                driver = db.query(DriverInfo).filter(DriverInfo.available == True).first()

                if ride and driver:
                    print(f"🎯 Match Found!")
                    print(f"   User ID: {ride.user_id}")
                    print(f"   Driver ID: {driver.driver_id}")
                    print(f"   From: {ride.source_location}")
                    print(f"   To: {ride.dest_location}")

                    # Update statuses
                    ride.status = "matched"
                    driver.available = False

                    # Create matched ride record with status="pending_notification"
                    matched = MatchedRide(
                        user_id=ride.user_id,
                        driver_id=driver.driver_id,
                        status="pending_notification"  # Use status to track notification
                    )
                    db.add(matched)
                    db.commit()
                    
                    print(f"   ✅ Match stored in database (ID: {matched.id})")
                else:
                    print("   ℹ️  No pending rides or available drivers")
                    
            finally:
                db.close()
                
        except Exception as e:
            print(f"   ⚠️  Matcher loop error: {e}")


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
    pending = db.query(MatchedRide).filter(MatchedRide.notified == False).all()
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)