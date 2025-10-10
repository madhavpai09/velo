from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from .connections import Base

class RideRequest(Base):
    __tablename__ = "ride_requests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    source_location = Column(String, nullable=False)  # Changed from 'pickup'
    dest_location = Column(String, nullable=False)    # Changed from 'drop'
    status = Column(String, default="pending")        # pending, matched
    created_at = Column(DateTime, default=datetime.utcnow)

class DriverInfo(Base):
    __tablename__ = "driver_info"
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, nullable=False, unique=True)
    available = Column(Boolean, default=True)
    current_location = Column(String)

class MatchedRide(Base):
    __tablename__ = "matched_rides"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    driver_id = Column(Integer, nullable=False)
    status = Column(String, default="ongoing")