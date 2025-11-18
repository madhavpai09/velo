#!/usr/bin/env python3
"""
Database cleanup script for VELO ride-sharing system
Run this before starting fresh testing
"""

import psycopg2
import sys

def cleanup_database():
    """Clean up old/stale data from database"""
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            dbname="Mini_Uber",
            user="Mini_Uber_user",
            password="password",
            host="localhost"
        )
        
        cursor = conn.cursor()
        
        print("🧹 Starting database cleanup...")
        print("=" * 60)
        
        # 1. Delete old matched rides
        cursor.execute("SELECT COUNT(*) FROM matched_rides")
        old_matches = cursor.fetchone()[0]
        cursor.execute("DELETE FROM matched_rides")
        print(f"✅ Deleted {old_matches} old matched rides")
        
        # 2. Delete old broadcasts
        cursor.execute("SELECT COUNT(*) FROM ride_broadcasts WHERE status != 'accepted'")
        old_broadcasts = cursor.fetchone()[0]
        cursor.execute("DELETE FROM ride_broadcasts WHERE status != 'accepted'")
        print(f"✅ Deleted {old_broadcasts} old broadcasts")
        
        # 3. Reset all drivers to available
        cursor.execute("SELECT COUNT(*) FROM driver_info WHERE available = FALSE")
        busy_drivers = cursor.fetchone()[0]
        cursor.execute("UPDATE driver_info SET available = TRUE")
        print(f"✅ Reset {busy_drivers} drivers to available")
        
        # 4. Clean up pending/broadcasting rides (optional - comment out if you want to keep them)
        cursor.execute("SELECT COUNT(*) FROM ride_requests WHERE status IN ('pending', 'broadcasting', 'matched')")
        pending_rides = cursor.fetchone()[0]
        cursor.execute("DELETE FROM ride_requests WHERE status IN ('pending', 'broadcasting', 'matched')")
        print(f"✅ Deleted {pending_rides} pending/matched rides")
        
        # 5. Optional: Clean up completed rides (uncomment if needed)
        # cursor.execute("DELETE FROM ride_requests WHERE status = 'completed'")
        # print("✅ Deleted completed rides")
        
        conn.commit()
        
        print("=" * 60)
        print("✅ Database cleanup complete!")
        print("\nRemaining data:")
        
        # Show what's left
        cursor.execute("SELECT COUNT(*) FROM ride_requests")
        rides_left = cursor.fetchone()[0]
        print(f"   Rides: {rides_left}")
        
        cursor.execute("SELECT COUNT(*) FROM driver_info")
        drivers_left = cursor.fetchone()[0]
        print(f"   Drivers: {drivers_left}")
        
        cursor.execute("SELECT COUNT(*) FROM matched_rides")
        matches_left = cursor.fetchone()[0]
        print(f"   Matches: {matches_left}")
        
        cursor.execute("SELECT COUNT(*) FROM ride_broadcasts")
        broadcasts_left = cursor.fetchone()[0]
        print(f"   Broadcasts: {broadcasts_left}")
        
        cursor.close()
        conn.close()
        
        print("\n🚀 Ready for fresh testing!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("\n⚠️  WARNING: This will delete test data from the database!")
    response = input("Continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        cleanup_database()
    else:
        print("Cancelled.")