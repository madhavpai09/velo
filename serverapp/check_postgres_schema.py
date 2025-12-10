import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://Mini_Uber_user:password@localhost/Mini_Uber"

def check_schema():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            # Check columns in driver_info
            result = connection.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'driver_info'"))
            columns = [row[0] for row in result]
            print(f"📋 driver_info columns: {columns}")
            
            required = ['vehicle_type', 'phone_number', 'vehicle_details', 'is_verified_safe']
            missing = [col for col in required if col not in columns]
            
            if missing:
                print(f"❌ Missing columns: {missing}")
            else:
                print("✅ Schema looks correct!")
            
    except Exception as e:
        print(f"❌ Check failed: {e}")

if __name__ == "__main__":
    check_schema()
