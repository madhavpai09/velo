import os
from sqlalchemy import create_engine, text, inspect, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
from datetime import datetime

# Load env vars
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://Mini_Uber_user:password@localhost/Mini_Uber"
)

def migrate_v2():
    print(f"🚀 Starting V2 Migration (School Pool Pass) on {DATABASE_URL}...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        inspector = inspect(engine)
        
        # 1. Add is_verified_safe to driver_info
        columns = [c['name'] for c in inspector.get_columns('driver_info')]
        if 'is_verified_safe' not in columns:
            print("➕ Adding is_verified_safe to driver_info...")
            try:
                conn.execute(text("ALTER TABLE driver_info ADD COLUMN is_verified_safe BOOLEAN DEFAULT FALSE"))
                print("✅ Added is_verified_safe")
            except Exception as e:
                print(f"❌ Failed to add is_verified_safe: {e}")
        else:
            print("✅ is_verified_safe already exists")

        # 2. Create new tables if they don't exist
        # We can use SQLAlchemy's create_all, but let's be explicit with raw SQL for robustness in this script
        # or better, use the models metadata if we can import them safely.
        # Let's use raw SQL to avoid import issues and ensure exact schema.

        # Student Profiles
        if not inspector.has_table("student_profiles"):
            print("➕ Creating table student_profiles...")
            conn.execute(text("""
                CREATE TABLE student_profiles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name VARCHAR NOT NULL,
                    school_name VARCHAR NOT NULL,
                    school_address VARCHAR NOT NULL,
                    home_address VARCHAR NOT NULL,
                    grade VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX idx_student_profiles_user_id ON student_profiles(user_id)"))
            print("✅ Created student_profiles")
        else:
            print("✅ student_profiles table already exists")

        # Subscriptions
        if not inspector.has_table("subscriptions"):
            print("➕ Creating table subscriptions...")
            conn.execute(text("""
                CREATE TABLE subscriptions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    student_id INTEGER NOT NULL,
                    status VARCHAR DEFAULT 'active',
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id)"))
            conn.execute(text("CREATE INDEX idx_subscriptions_student_id ON subscriptions(student_id)"))
            print("✅ Created subscriptions")
        else:
            print("✅ subscriptions table already exists")

        # Subscription Schedules
        if not inspector.has_table("subscription_schedules"):
            print("➕ Creating table subscription_schedules...")
            conn.execute(text("""
                CREATE TABLE subscription_schedules (
                    id SERIAL PRIMARY KEY,
                    subscription_id INTEGER NOT NULL,
                    day_of_week VARCHAR NOT NULL,
                    pickup_time VARCHAR NOT NULL,
                    ride_type VARCHAR NOT NULL
                )
            """))
            conn.execute(text("CREATE INDEX idx_subscription_schedules_subscription_id ON subscription_schedules(subscription_id)"))
            print("✅ Created subscription_schedules")
        else:
            print("✅ subscription_schedules table already exists")

        print("🎉 V2 Migration complete!")

if __name__ == "__main__":
    migrate_v2()
