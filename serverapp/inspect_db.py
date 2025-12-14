import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

from database.connections import SessionLocal
from database.models import RideRequest, MatchedRide, DriverInfo

def inspect_ride(ride_id):
    db = SessionLocal()
    try:
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
        print(f"   found {len(drivers)} available drivers")
        for d in drivers:
            print(f"   - Driver {d.driver_id}, Avail: {d.available}, Updated: {d.updated_at}, Safe: {d.is_verified_safe}")

    finally:
        db.close()

if __name__ == "__main__":
    inspect_ride(264)
