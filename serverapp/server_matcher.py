from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import requests
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database.connections import SessionLocal, engine
from database.models import Base, RideRequest, DriverInfo, MatchedRide

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Matcher Server")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def health():
    return {"message": "Matcher running on port 8001"}

@app.post("/check_rides/")
def match_rides(db: Session = Depends(get_db)):
    """Match pending rides with available drivers"""
    ride = db.query(RideRequest).filter(RideRequest.status == "pending").first()
    driver = db.query(DriverInfo).filter(DriverInfo.available == True).first()

    if not ride or not driver:
        return {"message": "No pending rides or available drivers"}

    # Update statuses
    ride.status = "matched"
    driver.available = False
    
    # Create matched ride record
    matched = MatchedRide(user_id=ride.user_id, driver_id=driver.driver_id)
    db.add(matched)
    db.commit()

    print(f"🎯 Match Found!")
    print(f"   User ID: {ride.user_id}")
    print(f"   Driver ID: {driver.driver_id}")
    print(f"   From: {ride.source_location}")
    print(f"   To: {ride.dest_location}")

    # Prepare match data
    match_data = {
        "user_id": ride.user_id,
        "driver_id": driver.driver_id,
        "ride_id": ride.id,
        "source_location": ride.source_location,
        "dest_location": ride.dest_location,
        "driver_location": driver.current_location
    }

    # Notify the notifier server which will handle user/driver notifications
    try:
        requests.post("http://localhost:8002/notify_match/", json=match_data, timeout=2)
    except Exception as e:
        print(f"⚠️  Could not notify clients: {e}")

    return {
        "message": "Ride matched successfully",
        "user_id": ride.user_id,
        "driver_id": driver.driver_id
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
