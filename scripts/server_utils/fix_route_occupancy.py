import sys
import os
from sqlalchemy import func

sys.path.insert(0, os.path.dirname(__file__))

from database.connections import SessionLocal
from database.models import SchoolRoute, SchoolPassSubscription

def fix_route_occupancy():
    db = SessionLocal()
    try:
        print("🔧 Starting Route Occupancy Repair...")
        
        # Get all routes
        routes = db.query(SchoolRoute).all()
        
        for route in routes:
            # Count active subscriptions for this route
            active_subs_count = db.query(SchoolPassSubscription).filter(
                SchoolPassSubscription.route_id == route.id,
                SchoolPassSubscription.status == 'active'
            ).count()
            
            print(f"Route: {route.route_name} (ID: {route.id})")
            print(f"  Current Stored Occupancy: {route.current_occupancy}")
            print(f"  Actual Active Subscriptions: {active_subs_count}")
            
            if route.current_occupancy != active_subs_count:
                print(f"  ⚠️ Mismatch detected! Updating occupancy to {active_subs_count}...")
                route.current_occupancy = active_subs_count
                db.commit() # Commit each change
                print("  ✅ Updated.")
            else:
                print("  ✅ Occupancy is correct.")
                
        print("\n🎉 Repair completed successfully!")
        
    except Exception as e:
        print(f"❌ Repair failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_route_occupancy()
