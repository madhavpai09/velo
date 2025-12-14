#!/usr/bin/env python3
"""
Clear all data from the database - use with caution!
This will delete all rides, matches, and driver info.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.connections import SessionLocal, engine
from database.models import RideRequest, DriverInfo, MatchedRide

def clear_database():
    """Clear all data from database"""
    db = SessionLocal()
    try:
        print("🗑️  Clearing database...")
        
        # Delete all matches
        matches_count = db.query(MatchedRide).count()
        db.query(MatchedRide).delete()
        print(f"   ✅ Deleted {matches_count} match(es)")
        
        # Delete all ride requests
        rides_count = db.query(RideRequest).count()
        db.query(RideRequest).delete()
        print(f"   ✅ Deleted {rides_count} ride request(s)")
        
        # Delete all drivers
        drivers_count = db.query(DriverInfo).count()
        db.query(DriverInfo).delete()
        print(f"   ✅ Deleted {drivers_count} driver(s)")
        
        db.commit()
        print("\n✅ Database cleared successfully!")
        print("   All rides, matches, and drivers have been removed.")
        
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("⚠️  WARNING: This will delete ALL data from the database!")
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() == "yes":
        clear_database()
    else:
        print("❌ Operation cancelled.")

