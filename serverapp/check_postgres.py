import os
from sqlalchemy import create_engine, text

# Use the same URL as in connections.py
DATABASE_URL = "postgresql://Mini_Uber_user:password@localhost/Mini_Uber"

def check_postgres():
    try:
        print(f"🔌 Testing connection to: {DATABASE_URL}")
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Connection successful!")
            
            # Check if tables exist
            result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result]
            print(f"📊 Existing tables: {tables}")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    check_postgres()
