#!/usr/bin/env python3
"""
Fix database schema by adding missing columns to matched_rides table
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from database.connections import engine

def fix_schema():
    """Add missing columns if they don't exist"""
    with engine.connect() as conn:
        # Add otp column if it doesn't exist
        try:
            conn.execute(text("ALTER TABLE matched_rides ADD COLUMN otp VARCHAR"))
            conn.commit()
            print("✅ Added otp column to matched_rides")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  otp column already exists")
            else:
                print(f"⚠️  Error adding otp column: {e}")
        
        # Add created_at column if it doesn't exist  
        try:
            conn.execute(text("ALTER TABLE matched_rides ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
            conn.commit()
            print("✅ Added created_at column to matched_rides")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  created_at column already exists")
            else:
                print(f"⚠️  Error adding created_at column: {e}")
    
    print("✅ Schema fix complete!")

if __name__ == "__main__":
    fix_schema()
