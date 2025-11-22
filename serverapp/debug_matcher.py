
import sys
import os
import time
sys.path.insert(0, os.path.dirname(__file__))

from database.connections import SessionLocal, engine
from database.models import Base, RideRequest, DriverInfo, MatchedRide

# Create tables
Base.metadata.create_all(bind=engine)

def debug_matcher():
    db = SessionLocal()
    try:
        print("🧹 Cleaning up old data...")
        db.query(RideRequest).delete()
        db.query(DriverInfo).delete()
        db.query(MatchedRide).delete()
        db.commit()

        print("🚗 Creating a test driver...")
        driver = DriverInfo(
            driver_id=1234,
            available=True,
            current_location="12.9716,77.5946"
        )
        db.add(driver)
        db.commit()
        print(f"   Driver created: {driver.driver_id} (Available: {driver.available})")

        print("👤 Creating a test ride request...")
        ride = RideRequest(
            user_id=999,
            source_location="A",
            dest_location="B",
            status="pending"
        )
        db.add(ride)
        db.commit()
        print(f"   Ride created: {ride.id} (Status: {ride.status})")

        print("\n🔄 Running matcher logic (simulated)...")
        
        # Re-query to simulate fresh state
        pending_ride = db.query(RideRequest).filter(RideRequest.status == "pending").first()
        if not pending_ride:
            print("❌ No pending ride found!")
            return

        available_drivers = db.query(DriverInfo).filter(DriverInfo.available == True).all()
        if not available_drivers:
            print("❌ No available drivers found!")
            return
        
        print(f"   Found {len(available_drivers)} available drivers.")
        
        # Simulate is_driver_online logic
        online_driver = None
        for d in available_drivers:
            print(f"   Checking driver {d.driver_id}...")
            # In this debug script, we assume the driver is 'online' because we just created it
            # and we are not testing the port check (which would fail without a running client)
            # But the code has a fallback:
            # "Driver not found via port check - could be web driver or offline Python client"
            # "Since driver.available is True (we filtered for it), trust the database"
            online_driver = d
            break
        
        if online_driver:
            print(f"✅ Match found with driver {online_driver.driver_id}")
            
            # Perform match
            pending_ride.status = "matched"
            online_driver.available = False
            
            matched = MatchedRide(
                user_id=pending_ride.user_id,
                driver_id=online_driver.driver_id,
                ride_id=pending_ride.id,
                status="pending_notification"
            )
            db.add(matched)
            db.commit()
            print(f"✅ Match record created: ID {matched.id}, Status: {matched.status}")
        else:
            print("❌ No online driver selected.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_matcher()
