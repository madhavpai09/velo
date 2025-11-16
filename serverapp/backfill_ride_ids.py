#!/usr/bin/env python3
"""
Backfill script to populate ride_id for existing matches that don't have it.
This helps fix existing matches in the database.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.connections import SessionLocal
from database.models import MatchedRide, RideRequest

def backfill_ride_ids():
    """Update existing matches to have ride_id where possible"""
    db = SessionLocal()
    try:
        # Find all matches without ride_id
        matches_without_ride_id = db.query(MatchedRide).filter(
            MatchedRide.ride_id == None
        ).all()
        
        if not matches_without_ride_id:
            print("✅ All matches already have ride_id")
            return
        
        print(f"📝 Found {len(matches_without_ride_id)} matches without ride_id")
        updated_count = 0
        
        for match in matches_without_ride_id:
            # Try to find the ride for this match
            # First try to find a matched ride for this user_id
            ride = db.query(RideRequest).filter(
                RideRequest.user_id == match.user_id,
                RideRequest.status == "matched"
            ).order_by(RideRequest.created_at.desc()).first()
            
            # If not found, try any ride for this user
            if not ride:
                ride = db.query(RideRequest).filter(
                    RideRequest.user_id == match.user_id
                ).order_by(RideRequest.created_at.desc()).first()
            
            if ride:
                match.ride_id = ride.id
                updated_count += 1
                print(f"   ✅ Updated match {match.id}: user_id={match.user_id}, ride_id={ride.id}")
            else:
                print(f"   ⚠️  Could not find ride for match {match.id}: user_id={match.user_id}")
        
        db.commit()
        print(f"\n✅ Successfully updated {updated_count} out of {len(matches_without_ride_id)} matches")
        
    except Exception as e:
        print(f"❌ Error during backfill: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔄 Backfilling ride_id for existing matches...")
    backfill_ride_ids()
    print("✅ Backfill complete!")

