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
from api.routes import router as api_router
from pydantic import BaseModel

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

# Schema for driver registration
class DriverRegister(BaseModel):
    driver_id: str
    name: str
    port: int
    location: dict

@app.get("/")
def health():
    return {"message": "Orchestrator running on port 8000"}

@app.post("/driver/register")
def register_driver(driver: DriverRegister, db: Session = Depends(get_db)):
    """Register a new driver with the dispatch system"""
    try:
        # Extract numeric ID from DRIVER-XXXX format
        numeric_id = int(driver.driver_id.replace("DRIVER-", ""))
        
        # Check if driver already exists
        existing = db.query(DriverInfo).filter(
            DriverInfo.driver_id == numeric_id
        ).first()
        
        location_str = f"{driver.location['lat']},{driver.location['lng']}"
        
        if existing:
            # Update existing driver
            existing.available = True
            existing.current_location = location_str
            message = "Driver re-registered successfully"
        else:
            # Create new driver
            new_driver = DriverInfo(
                driver_id=numeric_id,
                available=True,
                current_location=location_str
            )
            db.add(new_driver)
            message = "Driver registered successfully"
        
        db.commit()
        
        print(f"✅ {message}: {driver.driver_id} (Port: {driver.port})")
        
        return {
            "message": message,
            "driver_id": driver.driver_id,
            "status": "available",
            "location": location_str
        }
    except Exception as e:
        print(f"❌ Driver registration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/ride/")
def create_ride(ride: RideCreate, db: Session = Depends(get_db)):
    # Map 'pickup' and 'drop' to 'source_location' and 'dest_location'
    new = RideRequest(
        user_id=ride.user_id,
        source_location=ride.pickup,
        dest_location=ride.drop,
        status="pending"
    )
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