from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import asyncio
import requests
import sys
import os
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(__file__))

from database.connections import SessionLocal, engine
from database.models import Base, RideRequest, DriverInfo  # do NOT import MatchedRide ORM for write/selects here

Base.metadata.create_all(bind=engine)


def is_driver_online(driver_id: int, db=None) -> bool:
    """Check if driver is online - for web drivers, check database; for Python clients, check port"""
    if db is not None:
        driver = db.query(DriverInfo).filter(DriverInfo.driver_id == driver_id).first()
        if driver and driver.available:
            try:
                driver_port = driver_id
                response = requests.get(
                    f"http://localhost:{driver_port}/status",
                    timeout=0.5
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get('driver_id') == f"DRIVER-{driver_id}" and data.get('is_available', False)
            except:
                # Port doesn't exist or timed out -> assume web driver and trust DB
                pass
            return True
        return False

    # Fallback: port check
    try:
        driver_port = driver_id
        response = requests.get(
            f"http://localhost:{driver_port}/status",
            timeout=1
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('driver_id') == f"DRIVER-{driver_id}" and data.get('is_available', False)
        return False
    except Exception as e:
        print(f"   ⚠️  Driver {driver_id} port check failed: {e}")
        return False


# Background task to check for matches every 5 seconds
async def matcher_loop():
    """Background task that wakes every 5s and matches pending rides to available drivers."""
    while True:
        try:
            await asyncio.sleep(5)
            print("🔍 Auto-checking for pending rides...")

            db = SessionLocal()
            try:
                # Find a pending ride
                ride = db.query(RideRequest).filter(RideRequest.status == "pending").first()
                if not ride:
                    print("   ℹ️  No pending rides")
                    db.close()
                    continue

                print(f"   📍 Found pending ride (id: {ride.id}) from user {ride.user_id}")

                # Find available drivers (DB)
                available_drivers = db.query(DriverInfo).filter(DriverInfo.available == True).all()
                if not available_drivers:
                    print("   ℹ️  No available drivers in database")
                    db.close()
                    continue

                print(f"   👥 Found {len(available_drivers)} driver(s) in database, checking if online...")

                online_driver = None
                for driver in available_drivers:
                    print(f"   🔌 Checking driver {driver.driver_id}...")
                    if is_driver_online(driver.driver_id, db=db):
                        online_driver = driver
                        print(f"   ✅ Driver {driver.driver_id} is ONLINE and available!")
                        break
                    else:
                        # If port check failed but DB says available, treat as web driver
                        online_driver = driver
                        print(f"   ✅ Driver {driver.driver_id} is available (web driver or DB-only)")
                        break

                if not online_driver:
                    print("   ℹ️  No online drivers found")
                    db.close()
                    continue

                # Found a match
                print("\n🎯 Match Found!")
                print(f"   User ID: {ride.user_id}")
                print(f"   Driver ID: {online_driver.driver_id}")
                print(f"   From: {ride.source_location}")
                print(f"   To: {ride.dest_location}")

                # Update ride and driver statuses via ORM
                ride.status = "matched"
                online_driver.available = False
                db.add(ride)
                db.add(online_driver)
                db.commit()

                # Insert matched_rides using explicit SQL (avoid ORM mapped MatchedRide to prevent created_at issues)
                insert_sql = text("""
                    INSERT INTO matched_rides (user_id, driver_id, ride_id, status)
                    VALUES (:user_id, :driver_id, :ride_id, :status)
                    RETURNING id
                """)
                params = {
                    "user_id": ride.user_id,
                    "driver_id": online_driver.driver_id,
                    "ride_id": ride.id,
                    "status": "pending_notification"
                }
                try:
                    result = db.execute(insert_sql, params)
                    new_id_row = result.fetchone()
                    db.commit()
                    new_match_id = new_id_row[0] if new_id_row is not None else None
                    print(f"   ✅ Match stored in database (ID: {new_match_id})")
                except Exception as e:
                    db.rollback()
                    print(f"   ❌ Failed to insert matched_rides via raw SQL: {e}")
                    import traceback; traceback.print_exc()

            finally:
                db.close()

        except Exception as e:
            print(f"   ⚠️  Matcher loop error: {e}")
            import traceback
            traceback.print_exc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(matcher_loop())
    print("🔄 Matcher loop started (checking every 5 seconds).")
    yield
    task.cancel()
    print("🛑 Matcher loop stopped.")


app = FastAPI(title="Matcher Server", lifespan=lifespan)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def health():
    return {"message": "Matcher running on port 8001"}


@app.get("/matches/pending")
def get_pending_matches(db: Session = Depends(get_db)):
    """Get all matches that haven't been notified yet (read-only debug)."""
    # Use explicit select of known columns to avoid created_at select
    try:
        rows = db.execute(text("SELECT id, user_id, driver_id, ride_id, status FROM matched_rides WHERE status = :s"),
                          {"s": "pending_notification"}).fetchall()
        matches = [{"id": r[0], "user_id": r[1], "driver_id": r[2], "ride_id": r[3], "status": r[4]} for r in rows]
        return {"count": len(matches), "matches": matches}
    except Exception as e:
        print(f"   ⚠️  Error fetching pending matches: {e}")
        return {"count": 0, "matches": [], "error": str(e)}


@app.get("/drivers/online")
def check_online_drivers(db: Session = Depends(get_db)):
    """Debug endpoint: Check which drivers are actually online"""
    all_drivers = db.query(DriverInfo).all()
    results = []

    for driver in all_drivers:
        online = is_driver_online(driver.driver_id, db=db)
        results.append({
            "driver_id": driver.driver_id,
            "db_available": driver.available,
            "actually_online": online,
            "port": driver.driver_id,
            "type": "web" if driver.available and not online else "python_client"
        })

    return {"drivers": results}


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🎯 Mini Uber Matcher Service")
    print("="*60)
    print("   Port: 8001")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="warning")
