import sys
import os

# Add current directory to path so we can import serverapp
sys.path.append(os.getcwd())

from serverapp.server import get_db
from serverapp.database.models import DriverInfo, MatchedRide, RideRequest, SchoolPassSubscription

try:
    db = next(get_db())
    print("🔌 Connected to DB")

    # 1. Reset all drivers to AVAILABLE
    drivers = db.query(DriverInfo).all()
    count = 0
    for d in drivers:
        d.available = True
        count += 1
    db.commit()
    print(f"✅ Reset {count} drivers to AVAILABLE")

    # 2. Clear stuck matches
    matches = db.query(MatchedRide).filter(MatchedRide.status.in_(['accepted', 'in_progress'])).all()
    if matches:
        print(f"⚠️ Found {len(matches)} stuck matches. Clearing...")
        for m in matches:
            db.delete(m) # Or set to completed
        db.commit()
        print("✅ Stuck matches cleared")
    else:
        print("✅ No stuck matches found")

    # 3. Cancel pending/active rides
    rides = db.query(RideRequest).filter(RideRequest.status.in_(['pending', 'matched', 'in_progress'])).all()
    if rides:
        print(f"⚠️ Found {len(rides)} stuck rides. Marking cancelled...")
        for r in rides:
            r.status = 'cancelled'
        db.commit()
        print("✅ Stuck rides cancelled")
    else:
        print("✅ No stuck rides found")
            
except Exception as e:
    print(f"❌ Error: {e}")
