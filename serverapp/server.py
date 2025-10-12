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
        
        # Update ride status
        old_status = ride.status
        ride.status = status
        db.commit()
        
        print(f"📊 Ride {ride_id} status: {old_status} → {status}")
        
        # If ride completed, mark driver as available
        if status == "completed":
            # Find the matched ride to get driver_id
            matched = db.query(MatchedRide).filter(
                MatchedRide.user_id == ride.user_id
            ).first()
            
            if matched:
                driver = db.query(DriverInfo).filter(
                    DriverInfo.driver_id == matched.driver_id
                ).first()
                
                if driver:
                    driver.available = True
                    db.commit()
                    print(f"✅ Driver {matched.driver_id} is now available")
        
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
        matched = MatchedRide(user_id=payload.user_id, driver_id=payload.driver_id)
        db.add(matched)
        db.commit()
        db.refresh(matched)
        print(f"📝 Match recorded: User {payload.user_id} ↔ Driver {payload.driver_id}")
        return {"message": "match recorded", "matched_id": matched.id}
    else:
        print(f"ℹ️  Match already exists: User {payload.user_id} ↔ Driver {payload.driver_id}")
        return {"message": "match already exists", "matched_id": existing_match.id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)