from sqlalchemy import Column, Integer, String, DateTime, func
from database.connection import Base

class RideRequestDB(Base):
    __tablename__ = "ride_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    source_location = Column(String, nullable=False)
    dest_location = Column(String, nullable=False)
    user_id = Column(Integer, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())