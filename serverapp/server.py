from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
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
from datetime import datetime

Base.metadata.create_all(bind=engine)


# Define cleanup_on_startup FIRST
def cleanup_on_startup():
    """Clean up stale matches and reset ride/driver states on server startup"""
    db = SessionLocal()
    try:
        print("\n🧹 Performing startup cleanup...")
        
        old_matches = db.query(MatchedRide).filter(
            MatchedRide.status.in_(["pending_notification", "accepted"])
        ).all()
        
        if old_matches:
            print(f"   🗑️  Removing {len(old_matches)} old match(es)...")
            for match in old_matches:
                driver = db.query(DriverInfo).filter(
                    DriverInfo.driver_id == match.driver_id
                ).first()
                if driver and not driver.available:
                    driver.available = True
                db.delete(match)
        
        stuck_rides = db.query(RideRequest).filter(
            RideRequest.status.in_(["matched", "broadcasting"])
        ).all()
        
        if stuck_rides:
            print(f"   🗑️  Resetting {len(stuck_rides)} stuck ride(s)...")
            for ride in stuck_rides:
                ride.status = "pending"
        
        db.commit()
        print("   ✅ Cleanup complete\n")
    except Exception as e:
        print(f"   ⚠️  Cleanup error: {e}")
        db.rollback()
    finally:
        db.close()


# Define lifespan SECOND
@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_on_startup()
    yield


# Create app THIRD
app = FastAPI(title="Orchestrator Server", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

# Continue with the rest of the file...



# Startup event to clean up stale data
def cleanup_on_startup():
    """Clean up stale matches and reset ride/driver states on server startup"""
    db = SessionLocal()
    try:
        print("\n🧹 Performing startup cleanup...")
        
        # Clear all pending matches to avoid re-processing old matches
        old_matches = db.query(MatchedRide).filter(
            MatchedRide.status.in_(["pending_notification", "accepted"])
        ).all()
        
        if old_matches:
            print(f"   🗑️  Removing {len(old_matches)} old match(es) from previous session...")
            
            # Reset drivers marked as unavailable back to available
            for match in old_matches:
                driver = db.query(DriverInfo).filter(
                    DriverInfo.driver_id == match.driver_id
                ).first()
                if driver and not driver.available:
                    driver.available = True
                    print(f"      ✅ Driver {match.driver_id} marked available again")
                
                db.delete(match)
        
        # Reset all rides that are stuck in "matched" or "broadcasting" status
        stuck_rides = db.query(RideRequest).filter(
            RideRequest.status.in_(["matched", "broadcasting"])
        ).all()
        
        if stuck_rides:
            print(f"   🗑️  Resetting {len(stuck_rides)} ride(s) stuck in matched/broadcasting...")
            for ride in stuck_rides:
                ride.status = "pending"
                print(f"      ✅ Ride {ride.id} reset to pending")
        
        db.commit()
        print("   ✅ Cleanup complete\n")
        
    except Exception as e:
        print(f"   ⚠️  Cleanup error: {e}")
        db.rollback()
    finally:
        db.close()



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
        matched = db.query(MatchedRide).filter(MatchedRide.user_id == ride_request.user_id).first()
        driver_id = matched.driver_id if matched else None
        
        return {
            "id": ride_request.id,
            "source_location": ride_request.source_location,
            "dest_location": ride_request.dest_location,
            "user_id": ride_request.user_id,
            "status": ride_request.status,
            "created_at": ride_request.created_at.isoformat(),
            "driver_id": driver_id  # Add this line
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": f"Could not fetch ride request: {e}"}

@app.post("/driver/register")
def register_driver(driver: DriverRegister, db: Session = Depends(get_db)):
    """Register a new driver with the dispatch system - FIXED VERSION"""
    try:
        print(f"\n📥 Received registration request:")
        print(f"   driver_id: {driver.driver_id}")
        print(f"   name: {driver.name}")
        print(f"   port: {driver.port}")
        print(f"   location: {driver.location}")
        
        # FIX 1: Safe driver_id extraction
        raw_id = str(driver.driver_id).strip()
        
        # Handle both "DRIVER-1234" and "1234" formats
        if raw_id.upper().startswith("DRIVER-"):
            raw_id = raw_id[7:]  # Remove "DRIVER-" prefix (7 characters)
        
        # Validate not empty
        if not raw_id:
            print("❌ Error: Empty driver_id")
            raise HTTPException(
                status_code=400,
                detail="driver_id cannot be empty"
            )
        
        # Validate numeric
        try:
            numeric_id = int(raw_id)
        except ValueError as e:
            print(f"❌ Error: Non-numeric driver_id: {raw_id}")
            raise HTTPException(
                status_code=400,
                detail=f"driver_id must be numeric. Got: {driver.driver_id}"
            )
        
        # Validate positive
        if numeric_id <= 0:
            print(f"❌ Error: Negative or zero driver_id: {numeric_id}")
            raise HTTPException(
                status_code=400,
                detail=f"driver_id must be positive. Got: {numeric_id}"
            )
        
        print(f"✅ Parsed driver_id: {numeric_id}")
        
        # FIX 2: Safe location extraction
        try:
            if isinstance(driver.location, dict):
                lat = float(driver.location.get('lat', 0))
                lng = float(driver.location.get('lng', 0))
            else:
                print(f"❌ Error: Invalid location type: {type(driver.location)}")
                raise HTTPException(
                    status_code=400,
                    detail="location must be an object with lat and lng"
                )
            
            location_str = f"{lat},{lng}"
            print(f"✅ Parsed location: {location_str}")
            
        except (KeyError, ValueError, TypeError) as e:
            print(f"❌ Error parsing location: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid location format. Expected {{lat: number, lng: number}}"
            )
        
        # FIX 3: Safe database operations
        if db is None:
            print("⚠️  Warning: Database not available, simulating success")
            return {
                "message": "Driver registered successfully (no DB)",
                "driver_id": f"DRIVER-{numeric_id}",
                "numeric_id": numeric_id,
                "status": "available",
                "location": location_str
            }
        
        # Check if driver exists
        existing = db.query(DriverInfo).filter(
            DriverInfo.driver_id == numeric_id
        ).first()
        
        if existing:
            # Update existing driver
            existing.available = True
            existing.current_location = location_str
            message = "Driver re-registered successfully"
            print(f"🔄 Updated existing driver: {numeric_id}")
        else:
            # Create new driver
            new_driver = DriverInfo(
                driver_id=numeric_id,
                available=True,
                current_location=location_str
            )
            db.add(new_driver)
            message = "Driver registered successfully"
            print(f"✅ Created new driver: {numeric_id}")
        
        db.commit()
        
        result = {
            "message": message,
            "driver_id": f"DRIVER-{numeric_id}",
            "numeric_id": numeric_id,
            "status": "available",
            "location": location_str,
            "port": driver.port
        }
        
        print(f"✅ Registration successful: {result}")
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions (already have proper status codes)
        raise
        
    except Exception as e:
        # Catch ANY other error and return detailed 500
        error_msg = f"Unexpected error: {str(e)}"
        print(f"\n❌ CRITICAL ERROR in register_driver:")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {type(e).__name__}: {str(e)}"
        )

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

@app.post("/driver/heartbeat")
def driver_heartbeat(driver_id: str, db: Session = Depends(get_db)):
    """Update driver heartbeat"""
    try:
        numeric_id = int(driver_id.replace("DRIVER-", ""))
        driver = db.query(DriverInfo).filter(DriverInfo.driver_id == numeric_id).first()
        
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        # Explicitly update updated_at
        driver.updated_at = datetime.utcnow()
        db.commit()
        return {"status": "ok", "timestamp": driver.updated_at.isoformat()}
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
        
        # If ride completed, mark driver as available AND clean up match
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
                    print(f"✅ Driver {matched.driver_id} marked as AVAILABLE")
                
                # DELETE the match record so driver can be matched again
                db.delete(matched)
                db.commit()
                print(f"🗑️  Match record DELETED for driver {matched.driver_id}")
            else:
                print(f"⚠️  No match record found for ride {ride_id}")
        
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
        # Get ride_id from the ride if available
        ride_id = ride.id if ride else None
        matched = MatchedRide(
            user_id=payload.user_id, 
            driver_id=payload.driver_id,
            ride_id=ride_id  # Store ride_id for direct lookup
        )
        db.add(matched)
        db.commit()
        db.refresh(matched)
        print(f"📝 Match recorded: User {payload.user_id} ↔ Driver {payload.driver_id} (Ride ID: {ride_id})")
        return {"message": "match recorded", "matched_id": matched.id}
    else:
        # Update existing match with ride_id if not already set
        if ride and not existing_match.ride_id:
            existing_match.ride_id = ride.id
            db.commit()
        print(f"ℹ️  Match already exists: User {payload.user_id} ↔ Driver {payload.driver_id}")
        return {"message": "match already exists", "matched_id": existing_match.id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)