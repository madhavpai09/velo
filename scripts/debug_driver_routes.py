import sys
import os
from sqlalchemy import func
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))

from serverapp.database.connections import SessionLocal
from serverapp.database.models import SchoolPassSubscription, SubscriptionSchedule, SchoolRoute, StudentProfile

# Force Saturday for testing if needed, or use actual today
TODAY = date.today()
DAY_NAME = TODAY.strftime("%A").lower()
print(f"📅 Debugging for Date: {TODAY} ({DAY_NAME})")

def check_driver_routes(driver_id):
    db = SessionLocal()
    try:
        print(f"\n🔍 Checking routes for Driver {driver_id}...")
        
        # 1. Check Subscriptions
        subs = db.query(SchoolPassSubscription).filter(
            SchoolPassSubscription.assigned_driver_id == driver_id,
            SchoolPassSubscription.status == "active"
        ).all()
        
        print(f"   Found {len(subs)} active subscriptions.")
        for sub in subs:
            student = db.query(StudentProfile).filter(StudentProfile.id == sub.student_id).first()
            route = db.query(SchoolRoute).filter(SchoolRoute.id == sub.route_id).first()
            print(f"   - Sub ID: {sub.id}, Student: {student.name}, Route: {route.route_name} (ID: {sub.route_id})")
            
            # Check Schedules
            schedules = db.query(SubscriptionSchedule).filter(
                SubscriptionSchedule.subscription_id == sub.id
            ).all()
            print(f"     Assignments: {[s.day_of_week for s in schedules]}")
            
            # Check if there is a schedule for today
            today_sched = [s for s in schedules if s.day_of_week == DAY_NAME]
            if today_sched:
                print(f"     ✅ Scheduled for today ({DAY_NAME})!")
            else:
                print(f"     ❌ NOT scheduled for today ({DAY_NAME}).")
                
        # 2. Simulate API Logic (including fallback)
        print("\n🔄 Simulating API Query Logic...")
        target_days = [DAY_NAME, DAY_NAME[:3]]
        
        schedules = db.query(SubscriptionSchedule).join(
            SchoolPassSubscription,
            SubscriptionSchedule.subscription_id == SchoolPassSubscription.id
        ).filter(
            SchoolPassSubscription.assigned_driver_id == driver_id,
            SchoolPassSubscription.status == "active",
            SubscriptionSchedule.day_of_week.in_(target_days)
        ).all()
        
        if not schedules:
            print(f"   ⚠️ API Query returned EMPTY for {target_days}. Checking fallback to 'monday'...")
            fallback_days = ["monday", "mon"]
            schedules = db.query(SubscriptionSchedule).join(
                SchoolPassSubscription,
                SubscriptionSchedule.subscription_id == SchoolPassSubscription.id
            ).filter(
                SchoolPassSubscription.assigned_driver_id == driver_id,
                SchoolPassSubscription.status == "active",
                SubscriptionSchedule.day_of_week.in_(fallback_days)
            ).all()
             
            if schedules:
                 print(f"   ✅ Fallback found {len(schedules)} schedules for 'monday'.")
            else:
                 print(f"   ❌ Fallback also returned EMPTY.")
        else:
            print(f"   ✅ API Query found {len(schedules)} schedules for {DAY_NAME}.")

    finally:
        db.close()

if __name__ == "__main__":
    check_driver_routes(8101)
