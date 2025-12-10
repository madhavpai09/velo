import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://Mini_Uber_user:password@localhost/Mini_Uber"
)

def migrate_v4():
    print(f"🚀 Starting V4 Migration (Refinements) on {DATABASE_URL}...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        inspector = inspect(engine)
        
        # Add phone_number and vehicle_details to driver_info
        columns = [c['name'] for c in inspector.get_columns('driver_info')]
        
        if 'phone_number' not in columns:
            print("➕ Adding phone_number to driver_info...")
            try:
                conn.execute(text("ALTER TABLE driver_info ADD COLUMN phone_number VARCHAR"))
                print("✅ Added phone_number")
            except Exception as e:
                print(f"❌ Failed to add phone_number: {e}")
        
        if 'vehicle_details' not in columns:
            print("➕ Adding vehicle_details to driver_info...")
            try:
                conn.execute(text("ALTER TABLE driver_info ADD COLUMN vehicle_details VARCHAR"))
                print("✅ Added vehicle_details")
            except Exception as e:
                print(f"❌ Failed to add vehicle_details: {e}")

        print("🎉 V4 Migration complete!")

if __name__ == "__main__":
    migrate_v4()
