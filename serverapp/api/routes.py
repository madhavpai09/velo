from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.schemas import PingRequest, RideRequest as RideRequestSchema, RideRequestResponse, RideRequestCreate
from database.connections import get_db
from database.models import RideRequest as RideRequestModel, DriverInfo
from typing import List
import datetime

router = APIRouter()

@router.post("/ping")
def ping(request: PingRequest):
    """Original ping endpoint"""
    if request.data == "ping":
        return {"response": "pong"}
    return {"error": "invalid data"}

@router.post("/ride-request", response_model=dict)
def create_ride_request(ride_request: RideRequestSchema, db: Session = Depends(get_db)):
    """
    Create a new ride request
    """
    try:
        if db is None:
            # Fallback when database is not available
            print("📝 We will store this data in Postgres now")
            print(f"📍 Source: {ride_request.source_location}")
            print(f"📍 Destination: {ride_request.dest_location}")
            print(f"👤 User ID: {ride_request.user_id}")
            print(f"⏰ Timestamp: {datetime.datetime.now()}")
            return {
                "message": "Ride request received (simulated)",
                "data": {
                    "id": 999,
                    "source_location": ride_request.source_location,
                    "dest_location": ride_request.dest_location,
                    "user_id": ride_request.user_id,
                    "status": "pending",
                    "created_at": datetime.datetime.now().isoformat()
                }
            }
        
        # Create new ride request in database
        db_ride_request = RideRequestModel(
            source_location=ride_request.source_location,
            dest_location=ride_request.dest_location,
            user_id=ride_request.user_id,
            status="pending"
        )
        db.add(db_ride_request)
        db.commit()
        db.refresh(db_ride_request)
        
        print(f"✅ Ride request saved to Postgres with ID: {db_ride_request.id}")
        return {
            "message": "Ride request created successfully",
            "data": {
                "id": db_ride_request.id,
                "source_location": db_ride_request.source_location,
                "dest_location": db_ride_request.dest_location,
                "user_id": db_ride_request.user_id,
                "status": db_ride_request.status,
                "created_at": db_ride_request.created_at.isoformat()
            }
        }
    except Exception as e:
        print(f"❌ Error creating ride request: {e}")
        return {
            "message": "Ride request received (database error)",
            "error": str(e),
            "data": {
                "source_location": ride_request.source_location,
                "dest_location": ride_request.dest_location,
                "user_id": ride_request.user_id,
                "status": "pending"
            }
        }

@router.get("/ride-requests", response_model=List[dict])
def get_ride_requests(db: Session = Depends(get_db)):
    """Get all ride requests"""
    try:
        if db is None:
            return [{"message": "Database not connected - no ride requests to show"}]
        
        ride_requests = db.query(RideRequestModel).all()
        return [
            {
                "id": req.id,
                "source_location": req.source_location,
                "dest_location": req.dest_location,
                "user_id": req.user_id,
                "status": req.status,
                "created_at": req.created_at.isoformat()
            }
            for req in ride_requests
        ]
    except Exception as e:
        return [{"error": f"Could not fetch ride requests: {e}"}]

@router.get("/ride-request/{ride_id}")
def get_ride_request(ride_id: int, db: Session = Depends(get_db)):
    """Get a specific ride request by ID"""
    try:
        if db is None:
            return {"message": f"Would fetch ride request {ride_id} from Postgres"}
        
        ride_request = db.query(RideRequestModel).filter(RideRequestModel.id == ride_id).first()
        
        if not ride_request:
            raise HTTPException(status_code=404, detail="Ride request not found")
        
        return {
            "id": ride_request.id,
            "source_location": ride_request.source_location,
            "dest_location": ride_request.dest_location,
            "user_id": ride_request.user_id,
            "status": ride_request.status,
            "created_at": ride_request.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": f"Could not fetch ride request: {e}"}

@router.get("/drivers/available")
def get_available_drivers(db: Session = Depends(get_db)):
    """Get all available drivers"""
    try:
        if db is None:
            return {"message": "Database not connected", "drivers": []}
        
        available_drivers = db.query(DriverInfo).filter(DriverInfo.available == True).all()
        
        return {
            "count": len(available_drivers),
            "drivers": [
                {
                    "id": driver.id,
                    "driver_id": driver.driver_id,
                    "current_location": driver.current_location,
                    "available": driver.available
                }
                for driver in available_drivers
            ]
        }
    except Exception as e:
        return {"error": f"Could not fetch available drivers: {e}", "drivers": []}

@router.get("/drivers/{driver_id}")
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    """Get a specific driver by ID"""
    try:
        if db is None:
            return {"message": f"Would fetch driver {driver_id} from database"}
        
        driver = db.query(DriverInfo).filter(DriverInfo.driver_id == driver_id).first()
        
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        return {
            "id": driver.id,
            "driver_id": driver.driver_id,
            "current_location": driver.current_location,
            "available": driver.available
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": f"Could not fetch driver: {e}"}