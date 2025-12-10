import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://Mini_Uber_user:password@localhost/Mini_Uber"

def check_data():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT count(*) FROM schools"))
            count = result.scalar()
            print(f"🏫 School count: {count}")
            
    except Exception as e:
        print(f"❌ Check failed: {e}")

if __name__ == "__main__":
    check_data()
