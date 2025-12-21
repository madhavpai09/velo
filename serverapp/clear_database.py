#!/usr/bin/env python3
"""
Clear all data from the database - use with caution!
This will delete all data from all tables.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

try:
    from database.connections import SessionLocal, engine
    from database.models import (
        User, RideRequest, DriverInfo, MatchedRide, DriverRating,
        StudentProfile, Subscription, SubscriptionSchedule,
        School, SchoolRoute, RouteStop, SchoolPassSubscription,
        DriverRouteAssignment, PickupEvent
    )
    DB_AVAILABLE = True
except ImportError as e:
    print(f"❌ Database connection error: {e}")
    print("\n⚠️  Make sure:")
    print("   1. PostgreSQL is running")
    print("   2. psycopg2 is installed: pip install psycopg2-binary")
    print("   3. Database credentials are correct in .env file")
    DB_AVAILABLE = False

def clear_database():
    """Clear all data from database"""
    if not DB_AVAILABLE:
        print("\n❌ Cannot clear database - connection not available!")
        return
        
    db = SessionLocal()
    try:
        print("🗑️  Clearing database...")
        print("⚠️  This will delete ALL data from ALL tables!\n")
        
        # Delete in order to respect foreign key constraints
        # Delete child tables first, then parent tables
        
        # 1. Delete pickup events
        count = db.query(PickupEvent).count()
        db.query(PickupEvent).delete()
        print(f"   ✅ Deleted {count} pickup event(s)")
        
        # 2. Delete driver route assignments
        count = db.query(DriverRouteAssignment).count()
        db.query(DriverRouteAssignment).delete()
        print(f"   ✅ Deleted {count} driver route assignment(s)")
        
        # 3. Delete school pass subscriptions
        count = db.query(SchoolPassSubscription).count()
        db.query(SchoolPassSubscription).delete()
        print(f"   ✅ Deleted {count} school pass subscription(s)")
        
        # 4. Delete route stops
        count = db.query(RouteStop).count()
        db.query(RouteStop).delete()
        print(f"   ✅ Deleted {count} route stop(s)")
        
        # 5. Delete school routes
        count = db.query(SchoolRoute).count()
        db.query(SchoolRoute).delete()
        print(f"   ✅ Deleted {count} school route(s)")
        
        # 6. Delete schools
        count = db.query(School).count()
        db.query(School).delete()
        print(f"   ✅ Deleted {count} school(s)")
        
        # 7. Delete subscription schedules
        count = db.query(SubscriptionSchedule).count()
        db.query(SubscriptionSchedule).delete()
        print(f"   ✅ Deleted {count} subscription schedule(s)")
        
        # 8. Delete subscriptions
        count = db.query(Subscription).count()
        db.query(Subscription).delete()
        print(f"   ✅ Deleted {count} subscription(s)")
        
        # 9. Delete student profiles
        count = db.query(StudentProfile).count()
        db.query(StudentProfile).delete()
        print(f"   ✅ Deleted {count} student profile(s)")
        
        # 10. Delete driver ratings
        count = db.query(DriverRating).count()
        db.query(DriverRating).delete()
        print(f"   ✅ Deleted {count} driver rating(s)")
        
        # 11. Delete matched rides
        count = db.query(MatchedRide).count()
        db.query(MatchedRide).delete()
        print(f"   ✅ Deleted {count} matched ride(s)")
        
        # 12. Delete ride requests
        count = db.query(RideRequest).count()
        db.query(RideRequest).delete()
        print(f"   ✅ Deleted {count} ride request(s)")
        
        # 13. Delete drivers
        count = db.query(DriverInfo).count()
        db.query(DriverInfo).delete()
        print(f"   ✅ Deleted {count} driver(s)")
        
        # 14. Delete users (last, as other tables may reference it)
        count = db.query(User).count()
        db.query(User).delete()
        print(f"   ✅ Deleted {count} user(s)")
        
        db.commit()
        print("\n✅ Database cleared successfully!")
        print("   All data has been removed from all tables.")
        
    except Exception as e:
        print(f"\n❌ Error clearing database: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    if not DB_AVAILABLE:
        sys.exit(1)
        
    print("=" * 60)
    print("⚠️  WARNING: DATABASE CLEAR OPERATION")
    print("=" * 60)
    print("\nThis will permanently delete ALL data from the database:")
    print("  • All users and their accounts")
    print("  • All ride requests and history")
    print("  • All drivers and their information")
    print("  • All student profiles")
    print("  • All school pool subscriptions")
    print("  • All schools and routes")
    print("  • All ratings and reviews")
    print("  • Everything else!")
    print("\n⚠️  THIS CANNOT BE UNDONE!\n")
    print("=" * 60)
    
    response = input("\nType 'DELETE ALL' to confirm (or anything else to cancel): ")
    if response == "DELETE ALL":
        print("\n")
        clear_database()
    else:
        print("\n❌ Operation cancelled. Database remains unchanged.")
