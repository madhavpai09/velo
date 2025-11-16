from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.schemas import PingRequest, RideRequest as RideRequestSchema, RideRequestResponse, RideRequestCreate
from database.connections import get_db
from database.models import RideRequest as RideRequestModel, DriverInfo, MatchedRide
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
    """Create a new ride request"""
    try:
        if db is None:
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

@router.get("/driver/{driver_id}/pending-ride")
def get_pending_ride_for_driver(driver_id: int, db: Session = Depends(get_db)):
    """Get pending ride assignment for a driver (for web drivers to poll)"""
    try:
        # Find broadcast matches for this driver
        match = db.query(MatchedRide).filter(
            MatchedRide.driver_id == driver_id,
            MatchedRide.status == "broadcast"
        ).first()
        
        if not match:
            return {"has_ride": False}
        
        # Get ride details
        ride = db.query(RideRequestModel).filter(RideRequestModel.id == match.ride_id).first()
        if not ride:
            return {"has_ride": False}
        
        # Check if ride is still being broadcast (not yet accepted by another driver)
        if ride.status not in ["pending", "broadcasting"]:
            # Someone else accepted it
            db.delete(match)
            db.commit()
            return {"has_ride": False}
        
        return {
            "has_ride": True,
            "ride_id": ride.id,
            "user_id": match.user_id,
            "pickup_location": ride.source_location,
            "dropoff_location": ride.dest_location,
            "match_id": match.id
        }
    except Exception as e:
        return {"has_ride": False, "error": str(e)}

@router.get("/user/{user_id}/ride-status")
def get_user_ride_status(user_id: int, db: Session = Depends(get_db)):
    """Get ride status for a user (for web users to poll)"""
    try:
        # CRITICAL: Only show ride to user if it's been ACCEPTED by a driver
        # NOT during "broadcast" or "broadcasting" status
        match = db.query(MatchedRide).filter(
            MatchedRide.user_id == user_id,
            MatchedRide.status.in_(["accepted", "user_notified"])
        ).first()
        
        if match:
            # Get ride details
            ride = db.query(RideRequestModel).filter(RideRequestModel.id == match.ride_id).first()
            if not ride:
                return {"has_ride": False}
            
            # Double-check: ride must be accepted or in_progress, NOT broadcasting
            if ride.status not in ["accepted", "in_progress", "completed"]:
                print(f"   ⚠️ User {user_id} ride status is '{ride.status}' - not showing to user yet")
                return {"has_ride": False}
            
            # Get driver info
            driver = db.query(DriverInfo).filter(DriverInfo.driver_id == match.driver_id).first()
            
            return {
                "has_ride": True,
                "ride_id": ride.id,
                "status": ride.status,
                "driver_id": match.driver_id,
                "driver_location": driver.current_location if driver else None,
                "pickup_location": ride.source_location,
                "dropoff_location": ride.dest_location,
                "match_id": match.id
            }
        
        # Check if user has a ride that's accepted/in_progress (fallback)
        ride = db.query(RideRequestModel).filter(
            RideRequestModel.user_id == user_id,
            RideRequestModel.status.in_(["accepted", "in_progress"])
        ).order_by(RideRequestModel.created_at.desc()).first()
        
        if ride:
            driver_match = db.query(MatchedRide).filter(
                MatchedRide.user_id == user_id,
                MatchedRide.status.in_(["accepted", "user_notified"])
            ).first()
            driver_id = driver_match.driver_id if driver_match else None
            
            # If no accepted match found, don't show ride
            if not driver_id:
                return {"has_ride": False}
            
            driver = None
            if driver_id:
                driver = db.query(DriverInfo).filter(DriverInfo.driver_id == driver_id).first()
            
            return {
                "has_ride": True,
                "ride_id": ride.id,
                "status": ride.status,
                "driver_id": driver_id,
                "driver_location": driver.current_location if driver else None,
                "pickup_location": ride.source_location,
                "dropoff_location": ride.dest_location
            }
        
        # No accepted ride found - user should keep waiting
        return {"has_ride": False}
        
    except Exception as e:
        return {"has_ride": False, "error": str(e)}

@router.post("/driver/{driver_id}/accept-ride/{match_id}")
def accept_ride_assignment(driver_id: int, match_id: int, db: Session = Depends(get_db)):
    """Mark ride assignment as accepted by driver - FIRST TO ACCEPT WINS"""
    try:
        match = db.query(MatchedRide).filter(
            MatchedRide.id == match_id,
            MatchedRide.driver_id == driver_id
        ).first()
        
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Get the ride
        ride = db.query(RideRequestModel).filter(RideRequestModel.id == match.ride_id).first()
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        
        # CHECK: Is this ride still available? (not already accepted by another driver)
        if ride.status not in ["pending", "broadcasting"]:
            # Someone else already accepted this ride
            print(f"⚠️ Driver {driver_id} tried to accept ride {match.ride_id} but it was already accepted")
            db.delete(match)
            db.commit()
            raise HTTPException(status_code=409, detail="Ride already accepted by another driver")
        
        # FIRST TO ACCEPT WINS!
        print(f"🎉 Driver {driver_id} is FIRST to accept ride {match.ride_id}!")
        
        # Update ride status to accepted
        ride.status = "accepted"
        
        # Mark driver as unavailable (on a ride)
        driver = db.query(DriverInfo).filter(DriverInfo.driver_id == driver_id).first()
        if driver:
            driver.available = False
        
        # Update this match status to "accepted"
        match.status = "accepted"
        
        # DELETE all other broadcast matches for this ride
        other_matches = db.query(MatchedRide).filter(
            MatchedRide.ride_id == match.ride_id,
            MatchedRide.id != match.id
        ).all()
        
        for other_match in other_matches:
            print(f"   ❌ Removing broadcast for driver {other_match.driver_id}")
            db.delete(other_match)
        
        db.commit()
        
        print(f"✅ Driver {driver_id} accepted ride {match.ride_id}")
        print(f"   Removed {len(other_matches)} other broadcast(s)")
        print(f"   Match status updated to 'accepted' - notifier will notify user")
        
        return {"message": "Ride accepted - You got it!", "ride_id": match.ride_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error accepting ride for driver {driver_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/driver/{driver_id}/current-ride")
def get_driver_current_ride(driver_id: int, db: Session = Depends(get_db)):
    """Get current active ride for a driver"""
    try:
        # Find active match for this driver (accepted or user_notified)
        match = db.query(MatchedRide).filter(
            MatchedRide.driver_id == driver_id,
            MatchedRide.status.in_(["accepted", "user_notified"])
        ).first()
        
        if not match:
            return {"has_ride": False}
        
        # Get ride details
        ride = db.query(RideRequestModel).filter(RideRequestModel.id == match.ride_id).first()
        if not ride:
            return {"has_ride": False}
        
        # Only return if ride is not completed
        if ride.status in ["completed", "cancelled"]:
            return {"has_ride": False}
        
        return {
            "has_ride": True,
            "ride_id": ride.id,
            "user_id": match.user_id,
            "status": ride.status,
            "pickup_location": ride.source_location,
            "dropoff_location": ride.dest_location,
            "match_id": match.id
        }
    except Exception as e:
        return {"has_ride": False, "error": str(e)}

@router.post("/driver/{driver_id}/complete-ride/{ride_id}")
def complete_ride(driver_id: int, ride_id: int, db: Session = Depends(get_db)):
    """Complete a ride and mark driver as available again"""
    try:
        # First check if ride exists
        ride = db.query(RideRequestModel).filter(RideRequestModel.id == ride_id).first()
        if not ride:
            raise HTTPException(status_code=404, detail=f"Ride {ride_id} not found")
        
        # Verify the ride belongs to this driver by checking match
        match = db.query(MatchedRide).filter(
            MatchedRide.driver_id == driver_id,
            MatchedRide.ride_id == ride_id
        ).first()
        
        if not match:
            if ride.status in ["completed", "cancelled"]:
                raise HTTPException(status_code=400, detail=f"Ride {ride_id} is already {ride.status}")
            
            if ride.status not in ["accepted", "matched", "in_progress"]:
                raise HTTPException(status_code=403, detail="Ride is not in a state that can be completed")
        
        # Update ride status to completed
        ride.status = "completed"
        
        # Mark driver as available again
        driver = db.query(DriverInfo).filter(DriverInfo.driver_id == driver_id).first()
        if driver:
            driver.available = True
        else:
            raise HTTPException(status_code=404, detail=f"Driver {driver_id} not found")
        
        # Delete the match record if it exists
        if match:
            db.delete(match)
        
        db.commit()
        
        print(f"✅ Ride {ride_id} completed by driver {driver_id}. Driver is now available.")
        
        return {"message": "Ride completed", "ride_id": ride_id, "driver_available": True}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error completing ride {ride_id} for driver {driver_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to complete ride: {str(e)}")