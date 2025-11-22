import sys
sys.path.insert(0, '.')

from database.connections import SessionLocal
from database.models import RideRequest, DriverInfo, MatchedRide

db = SessionLocal()

# Check what we have
print("\n📊 Current State:")
drivers = db.query(DriverInfo).filter(DriverInfo.available == True).all()
print(f"Available drivers: {[d.driver_id for d in drivers]}")

rides = db.query(RideRequest).filter(RideRequest.status == "pending").all()
print(f"Pending rides: {[r.id for r in rides]}")

if drivers and rides:
    print(f"\n✅ We have {len(drivers)} driver(s) and {len(rides)} ride(s) - should match!")
    
    # Manually create a match
    driver = drivers[0]
    ride = rides[0]
    
    match = MatchedRide(
        user_id=ride.user_id,
        driver_id=driver.driver_id,
        ride_id=ride.id,
        status="pending_notification"
    )
    db.add(match)
    
    ride.status = "matched"
    driver.available = False
    
    db.commit()
    
    print(f"✅ Manually created match: User {ride.user_id} ↔ Driver {driver.driver_id}")
    print(f"   Match ID: {match.id}")
    print(f"\n🔔 Now the notifier should pick this up and notify both parties!")
else:
    print("\n❌ Missing driver or ride - cannot match")
    if not drivers:
        print("   No available drivers found")
        all_drivers = db.query(DriverInfo).all()
        if all_drivers:
            print(f"   BUT found {len(all_drivers)} total drivers:")
            for d in all_drivers:
                print(f"      - Driver {d.driver_id}: {'🟢 Available' if d.available else '🔴 Unavailable'}")
    if not rides:
        print("   No pending rides found")
        all_rides = db.query(RideRequest).all()
        if all_rides:
            print(f"   BUT found {len(all_rides)} total rides:")
            for r in all_rides:
                print(f"      - Ride {r.id}: Status {r.status}")

db.close()
