from serverapp.server import get_db
from serverapp.database.models import DriverInfo, MatchedRide, RideRequest, SchoolPassSubscription
from datetime import datetime

db = next(get_db())

print("\n--- DRIVERS ---")
drivers = db.query(DriverInfo).all()
for d in drivers:
    print(f"Driver {d.driver_id}: Avail={d.available}, Loc={d.current_location}")

print("\n--- ACTIVE RIDES (Matched) ---")
matches = db.query(MatchedRide).filter(MatchedRide.status.in_(['accepted', 'in_progress'])).all()
for m in matches:
    print(f"Match {m.id}: Ride {m.ride_id} -> Driver {m.driver_id} ({m.status})")

print("\n--- ACTIVE SUBSCRIPTIONS ---")
subs = db.query(SchoolPassSubscription).filter(SchoolPassSubscription.status == 'active').all()
for s in subs:
    print(f"Sub {s.id}: Student {s.student_id} -> Driver {s.assigned_driver_id}")
