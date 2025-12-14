import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime

# Define minimal models to read existing DB
Base = declarative_base()

class RideRequest(Base):
    __tablename__ = "ride_requests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    status = Column(String)
    ride_type = Column(String, default="auto")

class MatchedRide(Base):
    __tablename__ = "matched_rides"
    id = Column(Integer, primary_key=True, index=True)
    ride_id = Column(Integer)
    driver_id = Column(Integer)
    status = Column(String)
    created_at = Column(DateTime)

class DriverInfo(Base):
    __tablename__ = "driver_info"
    driver_id = Column(Integer, primary_key=True)
    available = Column(Boolean, default=True)
    updated_at = Column(DateTime)

# Connect to DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./rides.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def inspect_ride(ride_id):
    print(f"\n🔍 Inspecting Ride {ride_id}")
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride:
        print("   ❌ Ride not found")
        return
    print(f"   Status: {ride.status}")
    print(f"   User: {ride.user_id}")
    
    print("\n   matches:")
    matches = db.query(MatchedRide).filter(MatchedRide.ride_id == ride_id).all()
    for m in matches:
        print(f"   - Match {m.id}: Driver {m.driver_id}, Status '{m.status}', Created: {m.created_at}")
        
    print("\n   Available Drivers:")
    drivers = db.query(DriverInfo).filter(DriverInfo.available == True).all()
    for d in drivers:
        print(f"   - Driver {d.driver_id}, Avail: {d.available}, Updated: {d.updated_at}")

if __name__ == "__main__":
    inspect_ride(258)
