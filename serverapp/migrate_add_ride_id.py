#!/usr/bin/env python3
"""
Migration script to add ride_id column to matched_rides table.
Run this once to update your database schema.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.connections import engine
from sqlalchemy import text

def migrate():
    """Add ride_id column to matched_rides table if it doesn't exist"""
    try:
        with engine.connect() as conn:
            # Check if column already exists
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='matched_rides' AND column_name='ride_id'
            """)
            result = conn.execute(check_query)
            if result.fetchone():
                print("✅ Column 'ride_id' already exists in matched_rides table")
                return
            
            # Add the column
            alter_query = text("""
                ALTER TABLE matched_rides 
                ADD COLUMN ride_id INTEGER
            """)
            conn.execute(alter_query)
            conn.commit()
            print("✅ Successfully added 'ride_id' column to matched_rides table")
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("🔄 Running migration: Adding ride_id column to matched_rides table...")
    migrate()
    print("✅ Migration complete!")

