from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from .connections import Base

class RideRequest(Base):
    __tablename__ = "ride_requests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    source_location = Column(String, nullable=False)
    dest_location = Column(String, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

class DriverInfo(Base):
    __tablename__ = "driver_info"
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, nullable=False, unique=True)
    available = Column(Boolean, default=True)
    current_location = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MatchedRide(Base):
    __tablename__ = "matched_rides"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    driver_id = Column(Integer, nullable=False)
    ride_id = Column(Integer, nullable=True)
    status = Column(String, default="ongoing")
    created_at = Column(DateTime, default=datetime.utcnow)  # FIX: Added missing field
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)