from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://Mini_Uber_user:password@localhost/Mini_Uber"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    print("\n🔍 --- RECENT RIDES ---")
    rides = db.execute(text("""
        SELECT id, user_id, status, created_at 
        FROM ride_requests 
        ORDER BY created_at DESC 
        LIMIT 5
    """)).fetchall()
    
    for r in rides:
        print(f"   Ride {r.id}: User {r.user_id}, Status: {r.status}, Created: {r.created_at}")
    
    print("\n🤝 --- RECENT MATCHES ---")
    matches = db.execute(text("""
        SELECT id, ride_id, driver_id, status, otp
        FROM matched_rides 
        ORDER BY id DESC 
        LIMIT 5
    """)).fetchall()
    
    for m in matches:
        print(f"   Match {m.id}: Ride {m.ride_id} -> Driver {m.driver_id}, Status: {m.status}, OTP: {m.otp}")
        
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    db.close()
