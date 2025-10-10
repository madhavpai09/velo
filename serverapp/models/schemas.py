from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Ping schema
class PingRequest(BaseModel):
    data: str

# Ride Request schemas (for API routes)
class RideRequest(BaseModel):
    source_location: str
    dest_location: str
    user_id: int

class RideRequestCreate(BaseModel):
    source_location: str
    dest_location: str
    user_id: int

class RideRequestResponse(BaseModel):
    id: int
    source_location: str
    dest_location: str
    user_id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Original schemas (for orchestrator)
class RideCreate(BaseModel):
    user_id: int
    pickup: str
    drop: str

class DriverCreate(BaseModel):
    driver_id: int
    available: bool = True
    current_location: str | None = None

class UpdateMatchPayload(BaseModel):
    user_id: int
    driver_id: int