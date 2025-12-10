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

def migrate_v3():
    print(f"🚀 Starting V3 Migration (Enhancements) on {DATABASE_URL}...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        inspector = inspect(engine)
        
        # Add driver_id to subscriptions
        columns = [c['name'] for c in inspector.get_columns('subscriptions')]
        if 'driver_id' not in columns:
            print("➕ Adding driver_id to subscriptions...")
            try:
                conn.execute(text("ALTER TABLE subscriptions ADD COLUMN driver_id INTEGER"))
                print("✅ Added driver_id")
            except Exception as e:
                print(f"❌ Failed to add driver_id: {e}")
        else:
            print("✅ driver_id already exists")

        print("🎉 V3 Migration complete!")

if __name__ == "__main__":
    migrate_v3()
