import sys
import os
import json
from sqlalchemy import func

sys.path.insert(0, os.path.dirname(__file__))

from database.connections import SessionLocal
from database.models import SchoolRoute, SchoolPassSubscription, SubscriptionSchedule

def fix_missing_schedules():
    db = SessionLocal()
    try:
        print("🔧 Starting Schedule Backfill...")
        
        # Get all active school pass subscriptions
        subs = db.query(SchoolPassSubscription).filter(SchoolPassSubscription.status == 'active').all()
        
        for sub in subs:
            # Check if schedules exist
            count = db.query(SubscriptionSchedule).filter(SubscriptionSchedule.subscription_id == sub.id).count()
            
            if count == 0:
                print(f"⚠️ Subscription {sub.id} (Driver {sub.assigned_driver_id}) has NO schedules. Fixing...")
                
                # Get Route
                route = db.query(SchoolRoute).filter(SchoolRoute.id == sub.route_id).first()
                if not route or not route.days_of_week:
                    print(f"  ❌ Invalid route or no days defined for Sub {sub.id}")
                    continue
                    
                days = json.loads(route.days_of_week)
                for day in days:
                    schedule = SubscriptionSchedule(
                        subscription_id=sub.id,
                        day_of_week=day.lower(),
                        pickup_time=route.start_time,
                        ride_type=route.route_type
                    )
                    db.add(schedule)
                
                db.commit()
                print(f"  ✅ Created {len(days)} schedules for Sub {sub.id}.")
            else:
                print(f"✅ Subscription {sub.id} already has {count} schedules.")
                
        print("\n🎉 Backfill completed!")
        
    except Exception as e:
        print(f"❌ Backfill failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_missing_schedules()
