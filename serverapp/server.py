from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import random
from datetime import datetime
from pydantic import BaseModel
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from sqlalchemy.orm import Session
from database.connections import SessionLocal, engine
from database.models import Base, RideRequest, DriverInfo, MatchedRide
from models.schemas import RideCreate, DriverCreate, UpdateMatchPayload

# Create tables
Base.metadata.create_all(bind=engine)

# Create app WITHOUT lifespan to avoid issues
app = FastAPI(title="Orchestrator Server")

# Add CORS middleware AFTER app creation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
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
def read_root():
    return {"message": "Mini Uber API v3 - WORKING"}

@app.post("/driver/register")
def register_driver(driver: DriverRegister, db: Session = Depends(get_db)):
    """Register a new driver"""
    try:
        print(f"\n📥 Driver registration: {driver.driver_id}")
        
        raw_id = str(driver.driver_id).strip()
        if raw_id.upper().startswith("DRIVER-"):
            raw_id = raw_id[7:]
        
        numeric_id = int(raw_id)
        lat = float(driver.location.get('lat', 0))
        lng = float(driver.location.get('lng', 0))
        location_str = f"{lat},{lng}"
            
        existing = db.query(DriverInfo).filter(DriverInfo.driver_id == numeric_id).first()
        if existing:
            existing.available = True
            existing.current_location = location_str
            print(f"✅ Updated driver {numeric_id}")
        else:
            new_driver = DriverInfo(
                driver_id=numeric_id,
                available=True,
                current_location=location_str
            )
            db.add(new_driver)
            print(f"✅ Created driver {numeric_id}")
            
        db.commit()
        
        return {
            "message": "Driver registered successfully",
            "driver_id": f"DRIVER-{numeric_id}",
            "numeric_id": numeric_id,
            "status": "available",
            "location": location_str
        }
    except Exception as e:
        print(f"❌ Registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/driver/heartbeat")
def driver_heartbeat(driver_id: str, db: Session = Depends(get_db)):
    try:
        numeric_id = int(driver_id.replace("DRIVER-", ""))
        driver = db.query(DriverInfo).filter(DriverInfo.driver_id == numeric_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        driver.updated_at = datetime.utcnow()
        db.commit()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/driver/set-availability")
def set_driver_availability(driver_id: str, is_available: bool, db: Session = Depends(get_db)):
    try:
        numeric_id = int(driver_id.replace("DRIVER-", ""))
        driver = db.query(DriverInfo).filter(DriverInfo.driver_id == numeric_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        driver.available = is_available
        db.commit()
        print(f"✅ Driver {numeric_id} availability: {is_available}")
        return {"message": "Availability updated", "is_available": is_available}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ride/")
def create_ride(ride: RideCreate, db: Session = Depends(get_db)):
    new = RideRequest(
        user_id=ride.user_id,
        source_location=ride.pickup,
        dest_location=ride.drop,
        status="pending"
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    print(f"✅ Ride {new.id} created for user {ride.user_id}")
    return {"message": "ride created", "ride_id": new.id}

@app.post("/api/ride-request")
def create_ride_request(request: dict, db: Session = Depends(get_db)):
    """Frontend endpoint for creating ride requests"""
    try:
        # Accept both formats: {pickup, drop} or {source_location, dest_location}
        source = request.get('source_location') or request.get('pickup')
        dest = request.get('dest_location') or request.get('drop')
        user_id = request.get('user_id', 7000)
        
        if not source or not dest:
            raise HTTPException(status_code=400, detail="Missing location data")
        
        new = RideRequest(
            user_id=user_id,
            source_location=source,
            dest_location=dest,
            status="pending"
        )
        db.add(new)
        db.commit()
        db.refresh(new)
        print(f"✅ Ride request {new.id} created for user {user_id}")
        
        return {
            "message": "Ride request created successfully",
            "data": {
                "id": new.id,
                "source_location": new.source_location,
                "dest_location": new.dest_location,
                "user_id": new.user_id,
                "status": new.status,
                "created_at": new.created_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating ride: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/drivers/available")
def get_available_drivers(db: Session = Depends(get_db)):
    """Get all available drivers"""
    drivers = db.query(DriverInfo).filter(DriverInfo.available == True).all()
    return {
        "count": len(drivers),
        "drivers": [
            {
                "driver_id": d.driver_id,
                "location": d.current_location,
                "available": d.available
            }
            for d in drivers
        ]
    }

@app.get("/api/drivers/{driver_id}")
def get_driver_info(driver_id: int, db: Session = Depends(get_db)):
    """Get specific driver info"""
    driver = db.query(DriverInfo).filter(DriverInfo.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return {
        "driver_id": driver.driver_id,
        "location": driver.current_location,
        "available": driver.available
    }

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
        driver.updated_at = datetime.utcnow()
        db.commit()
        return {"message": "Location updated", "location": location_str}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/driver/{driver_id}/pending-ride")
def get_driver_pending_ride(driver_id: int, db: Session = Depends(get_db)):
    """Check if there's a pending ride OFFERED to this driver"""
    db.rollback()  # Fresh snapshot
    
    match = db.query(MatchedRide).filter(
        MatchedRide.driver_id == driver_id,
        MatchedRide.status == "offered"
    ).first()
    
    if not match:
        return {"has_ride": False}
        
    ride = db.query(RideRequest).filter(RideRequest.id == match.ride_id).first()
    if not ride:
        return {"has_ride": False}
        
    return {
        "has_ride": True,
        "match_id": match.id,
        "ride_id": ride.id,
        "user_id": ride.user_id,
        "pickup_location": ride.source_location,
        "dropoff_location": ride.dest_location,
        "status": "offered"
    }

@app.post("/api/driver/{driver_id}/accept-ride/{match_id}")
def accept_ride(driver_id: int, match_id: int, db: Session = Depends(get_db)):
    match = db.query(MatchedRide).filter(MatchedRide.id == match_id).first()
    if not match or match.driver_id != driver_id:
        raise HTTPException(status_code=404, detail="Match not found")
        
    ride = db.query(RideRequest).filter(RideRequest.id == match.ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
        
    otp = str(random.randint(1000, 9999))
    match.status = "accepted"
    match.otp = otp
    ride.status = "matched"
    
    driver = db.query(DriverInfo).filter(DriverInfo.driver_id == driver_id).first()
    if driver:
        driver.available = False
        
    db.commit()
    print(f"✅ Driver {driver_id} ACCEPTED ride {ride.id}. OTP: {otp}")
    return {"status": "accepted", "otp": otp}

@app.post("/api/ride/{ride_id}/verify-otp")
def verify_otp(ride_id: int, otp: str, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
        
    match = db.query(MatchedRide).filter(MatchedRide.ride_id == ride_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    if match.otp != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    ride.status = "in_progress"
    match.status = "in_progress"
    db.commit()
    print(f"🚀 Ride {ride_id} STARTED")
    return {"status": "in_progress", "message": "Ride started"}

@app.get("/api/driver/{driver_id}/current-ride")
def get_driver_current_ride(driver_id: int, db: Session = Depends(get_db)):
    match = db.query(MatchedRide).filter(
        MatchedRide.driver_id == driver_id,
        MatchedRide.status.in_(["accepted", "in_progress"])
    ).first()
    
    if not match:
        return {"has_ride": False}
        
    ride = db.query(RideRequest).filter(RideRequest.id == match.ride_id).first()
    if not ride:
        return {"has_ride": False}
        
    return {
        "has_ride": True,
        "ride_id": ride.id,
        "user_id": ride.user_id,
        "pickup_location": ride.source_location,
        "dropoff_location": ride.dest_location,
        "status": match.status,
        "otp": match.otp
    }

@app.get("/api/user/{user_id}/ride-status")
def get_user_ride_status(user_id: int, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(
        RideRequest.user_id == user_id
    ).order_by(RideRequest.created_at.desc()).first()
    
    if not ride:
        return {"has_ride": False}
        
    match = db.query(MatchedRide).filter(MatchedRide.ride_id == ride.id).first()
    
    response = {
        "has_ride": True,
        "ride_id": ride.id,
        "status": ride.status,
        "pickup_location": ride.source_location,
        "dropoff_location": ride.dest_location,
    }
    
    if match:
        response["driver_id"] = match.driver_id
        response["otp"] = match.otp
        driver = db.query(DriverInfo).filter(DriverInfo.driver_id == match.driver_id).first()
        if driver:
            response["driver_location"] = driver.current_location
            
    return response

@app.post("/api/driver/{driver_id}/complete-ride/{ride_id}")
def complete_ride(driver_id: int, ride_id: int, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
        
    match = db.query(MatchedRide).filter(MatchedRide.ride_id == ride_id).first()
    
    ride.status = "completed"
    if match:
        db.delete(match)
        
    driver = db.query(DriverInfo).filter(DriverInfo.driver_id == driver_id).first()
    if driver:
        driver.available = True
        
    db.commit()
    print(f"🏁 Ride {ride_id} COMPLETED")
    return {"status": "completed"}

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚗 Mini Uber Main Server")
    print("="*60)
    print("   Port: 8000")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")