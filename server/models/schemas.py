from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PingRequest(BaseModel):
    data: str

class RideRequest(BaseModel):
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

class RideRequestCreate(BaseModel):
    source_location: str
    dest_location: str
    user_id: int
    status: str = "pending"