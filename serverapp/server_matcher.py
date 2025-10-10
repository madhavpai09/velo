from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import requests

from connections import SessionLocal, engine
from models import Base, RideRequest, DriverInfo, MatchedRide

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
    ride = db.query(RideRequest).filter(RideRequest.status == "pending").first()
    driver = db.query(DriverInfo).filter(DriverInfo.available == True).first()

    if not ride or not driver:
        return {"message": "No pending rides or drivers"}

    ride.status = "matched"
    driver.available = False
    matched = MatchedRide(user_id=ride.user_id, driver_id=driver.driver_id)
    db.add(matched)
    db.commit()

    # Notify server 8002
    requests.post("http://localhost:8002/notify_match/", json={
        "user_id": ride.user_id,
        "driver_id": driver.driver_id
    })

    return {"message": "Ride matched", "user_id": ride.user_id, "driver_id": driver.driver_id}

