from fastapi import FastAPI, Depends, HTTPException
import requests
import time
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.connections import SessionLocal, engine
from database.models import Base, RideRequest, DriverInfo, MatchedRide
from models.schemas import RideCreate, DriverCreate, UpdateMatchPayload
from api.routes import router as api_router  # Add this import

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Orchestrator Server")

# Include the API router with /api prefix
app.include_router(api_router, prefix="/api")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def health():
    return {"message": "Orchestrator running on port 8000"}

@app.post("/ride/")
def create_ride(ride: RideCreate, db: Session = Depends(get_db)):
    new = RideRequest(**ride.model_dump())
    db.add(new)
    db.commit()
    db.refresh(new)
    return {"message": "ride created", "ride_id": new.id}

@app.post("/driver/")
def upsert_driver(driver: DriverCreate, db: Session = Depends(get_db)):
    existing = db.query(DriverInfo).filter(DriverInfo.driver_id == driver.driver_id).first()
    if existing:
        existing.available = driver.available
        existing.current_location = driver.current_location
    else:
        db.add(DriverInfo(**driver.model_dump()))
    db.commit()
    return {"message": "driver upserted", "driver_id": driver.driver_id}

@app.post("/update_match/")
def update_match(payload: UpdateMatchPayload, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(RideRequest.user_id == payload.user_id).first()
    driver = db.query(DriverInfo).filter(DriverInfo.driver_id == payload.driver_id).first()
    if ride:
        ride.status = "matched"
    if driver:
        driver.available = False
    matched = MatchedRide(user_id=payload.user_id, driver_id=payload.driver_id)
    db.add(matched)
    db.commit()
    db.refresh(matched)
    # Notify clients (best effort)
    try:
        requests.post("http://localhost:6000/match_update", json=payload.model_dump(), timeout=2)
        requests.post("http://localhost:9000/match_update", json=payload.model_dump(), timeout=2)
    except Exception:
        pass
    return {"message": "match recorded", "matched_id": matched.id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)