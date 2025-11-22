"""
Fixed Database Models
All missing columns added, proper types defined
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from .connections import Base

class RideRequest(Base):
    """Ride request model with all required fields"""
    __tablename__ = "ride_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    source_location = Column(String, nullable=False)
    dest_location = Column(String, nullable=False)
    status = Column(String, default="pending", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class DriverInfo(Base):
    """Driver information model"""
    __tablename__ = "driver_info"
    
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, nullable=False, unique=True, index=True)
    available = Column(Boolean, default=True, index=True)
    current_location = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MatchedRide(Base):
    """
    Matched ride model - connects users with drivers
    FIXED: Added all missing columns (otp, ride_id, created_at)
    """
    __tablename__ = "matched_rides"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    driver_id = Column(Integer, nullable=False, index=True)
    ride_id = Column(Integer, nullable=True, index=True)  # FIX: Added for direct ride lookup
    otp = Column(String, nullable=True)  # FIX: Added for user-driver verification
    status = Column(String, default="pending_notification", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # FIX: Added for stale detection
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)