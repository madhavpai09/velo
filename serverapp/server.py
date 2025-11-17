from fastapi import FastAPI, Depends, HTTPException
import requests
import time
import sys
import os
import random
sys.path.insert(0, os.path.dirname(__file__))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.connections import SessionLocal, engine
from database.models import Base, RideRequest, DriverInfo, MatchedRide
from models.schemas import RideCreate, DriverCreate, UpdateMatchPayload
from api.routes import router as api_router
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Orchestrator Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/api/ride-request/{ride_id}")
def get_ride_request(ride_id: int, db: Session = Depends(get_db)):
    """Get a specific ride request by ID"""
    try:
        ride_request = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
        
        if not ride_request:
            raise HTTPException(status_code=404, detail="Ride request not found")
        
        # Get matched driver if exists
        matched = db.query(MatchedRide).filter(MatchedRide.ride_id == ride_request.id).first()
        driver_id = matched.driver_id if matched else None
        
        return {
            "id": ride_request.id,
            "source_location": ride_request.source_location,
            "dest_location": ride_request.dest_location,
            "user_id": ride_request.user_id,
            "status": ride_request.status,
            "created_at": ride_request.created_at.isoformat(),
            "driver_id": driver_id
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": f"Could not fetch ride request: {e}"}

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

@app.post("/driver/update-location")
def update_driver_location(driver_id: str, location: dict, db: Session = Depends(get_db)):
    """Update driver location"""
    try:
        numeric_id = int(driver_id.replace("DRIVER-", ""))
        driver = db.query(DriverInfo).filter(DriverInfo.driver_id == numeric_id).first()
        
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        location_str = f"{location['lat']},{location['lng']}"
        driver.current_location = location_str
        db.commit()
        
        return {"message": "Location updated", "location": location_str}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/driver/set-availability")
def set_driver_availability(driver_id: str, is_available: bool, db: Session = Depends(get_db)):
    """Set driver availability"""
    try:
        numeric_id = int(driver_id.replace("DRIVER-", ""))
        driver = db.query(DriverInfo).filter(DriverInfo.driver_id == numeric_id).first()
        
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        driver.available = is_available
        db.commit()
        
        print(f"📊 Driver {driver_id} availability: {is_available}")
        
        return {"message": "Availability updated", "is_available": is_available}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ride/{ride_id}/update-status")
def update_ride_status(ride_id: int, status: str, db: Session = Depends(get_db)):
    """Update ride status (accepted, in_progress, completed, etc.)"""
    try:
        ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
        
        if not ride:
            raise HTTPException(status_code=404, detail=f"Ride {ride_id} not found")
        
        old_status = ride.status
        ride.status = status
        db.commit()
        
        print(f"📊 Ride {ride_id} status: {old_status} → {status}")
        
        return {
            "message": "Ride status updated",
            "ride_id": ride_id,
            "status": status
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    
    # Check if match already exists
    existing_match = db.query(MatchedRide).filter(
        MatchedRide.user_id == payload.user_id,
        MatchedRide.driver_id == payload.driver_id
    ).first()
    
    if not existing_match:
        ride_id = ride.id if ride else None
        matched = MatchedRide(
            user_id=payload.user_id, 
            driver_id=payload.driver_id,
            ride_id=ride_id,
            status="pending_notification"
        )
        db.add(matched)
        db.commit()
        db.refresh(matched)
        print(f"📝 Match recorded: User {payload.user_id} ↔ Driver {payload.driver_id} (Ride ID: {ride_id})")
        return {"message": "match recorded", "matched_id": matched.id}
    else:
        if ride and not existing_match.ride_id:
            existing_match.ride_id = ride.id
            db.commit()
        print(f"ℹ️  Match already exists: User {payload.user_id} ↔ Driver {payload.driver_id}")
        return {"message": "match already exists", "matched_id": existing_match.id}

ride_otps: Dict[int, str] = {}

@app.post("/api/ride/{ride_id}/generate-otp")
async def generate_ride_otp(ride_id: int):
    """Generate OTP for ride start verification"""
    otp = str(random.randint(1000, 9999))
    ride_otps[ride_id] = otp
    print(f"🔐 Generated OTP {otp} for ride {ride_id}")
    return {
        "ride_id": ride_id,
        "otp": otp,
        "message": "OTP generated successfully"
    }

@app.post("/api/ride/{ride_id}/verify-otp")
async def verify_ride_otp(ride_id: int, otp: str):
    """Verify OTP before starting ride"""
    stored_otp = ride_otps.get(ride_id)
    
    if not stored_otp:
        raise HTTPException(status_code=404, detail="No OTP found for this ride")
    
    if stored_otp != otp:
        return {
            "verified": False,
            "message": "Invalid OTP"
        }
    
    # OTP verified, remove it
    del ride_otps[ride_id]
    print(f"✅ OTP verified for ride {ride_id}")
    
    return {
        "verified": True,
        "message": "OTP verified successfully"
    }

@app.post("/api/driver/{driver_id}/start-ride/{ride_id}")
async def start_ride(driver_id: int, ride_id: int, db: Session = Depends(get_db)):
    """Start a ride after OTP verification"""
    try:
        ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        
        # Update ride status to in_progress
        ride.status = "in_progress"
        
        # Update match status
        match = db.query(MatchedRide).filter(
            MatchedRide.ride_id == ride_id,
            MatchedRide.driver_id == driver_id
        ).first()
        if match:
            match.status = "in_progress"
        
        db.commit()
        
        print(f"🚗 Ride {ride_id} started by driver {driver_id}")
        
        return {
            "message": "Ride started",
            "ride_id": ride_id,
            "status": "in_progress"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)