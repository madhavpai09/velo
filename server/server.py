from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import httpx
from datetime import datetime

app = FastAPI()

# ===== EXISTING DATA MODELS (Keep your existing ones) =====
class PingRequest(BaseModel):
    data: str

class RideRequest(BaseModel):
    source_location: str
    dest_location: str
    user_id: int

# ===== NEW DATA MODELS FOR MULTI-CLIENT SUPPORT =====
class DriverRegistration(BaseModel):
    driver_id: str
    name: str
    port: int
    location: Dict[str, float]  # {"lat": 0.0, "lng": 0.0}
    phone: Optional[str] = None

class DriverLocation(BaseModel):
    driver_id: str
    location: Dict[str, float]

class DriverAvailability(BaseModel):
    driver_id: str
    is_available: bool

class RideAssignment(BaseModel):
    ride_id: str
    driver_id: str
    driver_name: str
    driver_port: int
    user_id: int
    source_location: str
    dest_location: str
    status: str
    created_at: str

# ===== IN-MEMORY STORAGE =====
# Your existing ride requests storage
ride_requests = []
ride_request_id_counter = 1

# New storage for drivers and assignments
registered_drivers: Dict[str, dict] = {}
ride_assignments: Dict[str, RideAssignment] = {}

# ===== YOUR EXISTING ENDPOINTS (Keep as is) =====
@app.post("/api/ping")
async def ping(request: PingRequest):
    """Your existing ping endpoint"""
    return {
        "status": "success",
        "message": "pong",
        "received": request.data
    }

@app.post("/api/ride-request")
async def create_ride_request(request: RideRequest):
    """
    Your EXISTING endpoint - now enhanced to assign drivers
    This is what PostMan will call
    """
    global ride_request_id_counter
    
    # Store ride request (your existing logic)
    ride_data = {
        "id": ride_request_id_counter,
        "source_location": request.source_location,
        "dest_location": request.dest_location,
        "user_id": request.user_id,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    ride_requests.append(ride_data)
    
    # NEW: Try to assign to an available driver
    available_drivers = [d for d in registered_drivers.values() if d.get("is_available", False)]
    
    if available_drivers:
        # Assign to first available driver
        driver = available_drivers[0]
        
        # Create assignment
        assignment = RideAssignment(
            ride_id=f"RIDE-{ride_request_id_counter:04d}",
            driver_id=driver["driver_id"],
            driver_name=driver["name"],
            driver_port=driver["port"],
            user_id=request.user_id,
            source_location=request.source_location,
            dest_location=request.dest_location,
            status="assigned",
            created_at=datetime.now().isoformat()
        )
        
        ride_assignments[assignment.ride_id] = assignment
        ride_data["status"] = "assigned"
        ride_data["driver_id"] = driver["driver_id"]
        ride_data["driver_name"] = driver["name"]
        
        # Mark driver as unavailable
        registered_drivers[driver["driver_id"]]["is_available"] = False
        
        # Notify driver (async)
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"http://localhost:{driver['port']}/ride/assigned",
                    json={
                        "ride_id": assignment.ride_id,
                        "user_id": request.user_id,
                        "pickup_location": request.source_location,
                        "dropoff_location": request.dest_location
                    },
                    timeout=5.0
                )
        except Exception as e:
            print(f"Failed to notify driver: {e}")
        
        ride_request_id_counter += 1
        
        return {
            "status": "success",
            "message": "Ride request created and driver assigned",
            "ride_id": ride_data["id"],
            "ride_assignment_id": assignment.ride_id,
            "data": ride_data,
            "driver": {
                "id": driver["driver_id"],
                "name": driver["name"],
                "location": driver.get("location")
            }
        }
    else:
        # No drivers available - just create request
        ride_request_id_counter += 1
        
        return {
            "status": "success",
            "message": "Ride request created - waiting for driver",
            "ride_id": ride_data["id"],
            "data": ride_data,
            "note": "No drivers currently available"
        }

@app.get("/api/ride-requests")
async def get_ride_requests():
    """Your existing endpoint to get all ride requests"""
    return {
        "status": "success",
        "count": len(ride_requests),
        "data": ride_requests
    }

@app.get("/api/ride-request/{ride_id}")
async def get_ride_request(ride_id: int):
    """Your existing endpoint to get specific ride request"""
    for ride in ride_requests:
        if ride["id"] == ride_id:
            return {
                "status": "success",
                "data": ride
            }
    
    raise HTTPException(status_code=404, detail="Ride request not found")

# ===== NEW ENDPOINTS FOR MULTI-CLIENT SUPPORT =====

@app.post("/api/driver/register")
async def register_driver(driver: DriverRegistration):
    """NEW: Register a driver client"""
    registered_drivers[driver.driver_id] = {
        "driver_id": driver.driver_id,
        "name": driver.name,
        "port": driver.port,
        "location": driver.location,
        "phone": driver.phone,
        "is_available": True,
        "registered_at": datetime.now().isoformat()
    }
    
    print(f"✅ Driver registered: {driver.name} ({driver.driver_id}) on port {driver.port}")
    
    return {
        "status": "success",
        "message": "Driver registered successfully",
        "driver_id": driver.driver_id
    }

@app.post("/api/driver/update-location")
async def update_driver_location(update: DriverLocation):
    """NEW: Driver updates their location"""
    if update.driver_id not in registered_drivers:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    registered_drivers[update.driver_id]["location"] = update.location
    
    return {
        "status": "success",
        "message": "Location updated"
    }

@app.post("/api/driver/set-availability")
async def set_driver_availability(update: DriverAvailability):
    """NEW: Driver sets their availability"""
    if update.driver_id not in registered_drivers:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    registered_drivers[update.driver_id]["is_available"] = update.is_available
    
    return {
        "status": "success",
        "message": f"Driver availability set to {update.is_available}"
    }

@app.get("/api/drivers")
async def get_all_drivers():
    """NEW: Get all registered drivers"""
    return {
        "status": "success",
        "count": len(registered_drivers),
        "data": list(registered_drivers.values())
    }

@app.get("/api/drivers/available")
async def get_available_drivers():
    """NEW: Get only available drivers"""
    available = [d for d in registered_drivers.values() if d.get("is_available", False)]
    
    return {
        "status": "success",
        "count": len(available),
        "data": available
    }

@app.post("/api/ride/{ride_id}/status")
async def update_ride_status(ride_id: str, status: str):
    """NEW: Update ride status (called by driver)"""
    if ride_id not in ride_assignments:
        raise HTTPException(status_code=404, detail="Ride assignment not found")
    
    ride_assignments[ride_id].status = status
    
    # If ride completed, make driver available
    if status == "completed":
        driver_id = ride_assignments[ride_id].driver_id
        if driver_id in registered_drivers:
            registered_drivers[driver_id]["is_available"] = True
            print(f"✅ Ride {ride_id} completed. Driver {driver_id} is now available.")
    
    return {
        "status": "success",
        "message": "Ride status updated",
        "ride_id": ride_id,
        "new_status": status
    }

@app.get("/api/ride-assignment/{ride_id}")
async def get_ride_assignment(ride_id: str):
    """NEW: Get ride assignment details"""
    if ride_id not in ride_assignments:
        raise HTTPException(status_code=404, detail="Ride assignment not found")
    
    return {
        "status": "success",
        "data": ride_assignments[ride_id]
    }

@app.get("/")
async def root():
    """Root endpoint with system stats"""
    return {
        "service": "Mini Uber API",
        "version": "2.0",
        "total_drivers": len(registered_drivers),
        "available_drivers": len([d for d in registered_drivers.values() if d.get("is_available", False)]),
        "total_rides": len(ride_requests),
        "active_assignments": len([r for r in ride_assignments.values() if r.status not in ["completed", "cancelled"]])
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Mini Uber Server on port 8000")
    print("📝 Existing endpoints: /api/ping, /api/ride-request, /api/ride-requests")
    print("🆕 New endpoints: /api/driver/register, /api/drivers/available, etc.")
    uvicorn.run(app, host="0.0.0.0", port=8000)