from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import requests
import asyncio
import sys
import os
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(__file__))

from database.connections import SessionLocal, engine
from database.models import Base, RideRequest, DriverInfo  # avoid MatchedRide ORM for operations that touch created_at

Base.metadata.create_all(bind=engine)


# Background task to check for unnotified matches every 3 seconds
async def notifier_loop():
    """Background task that checks matched_rides table and notifies clients."""
    await asyncio.sleep(2)  # Initial delay
    print("🔍 Notifier starting checks...")

    while True:
        try:
            await asyncio.sleep(3)

            db = SessionLocal()
            try:
                # Select only known columns (avoid selecting created_at)
                rows = db.execute(text(
                    "SELECT id, user_id, driver_id, ride_id, status FROM matched_rides WHERE status = :s"
                ), {"s": "pending_notification"}).fetchall()

                if rows:
                    print(f"\n📢 Found {len(rows)} unnotified match(es)")
                else:
                    print(".", end="", flush=True)

                # Process each match row as a dict (avoid ORM object)
                for r in rows:
                    match = {
                        "id": r[0],
                        "user_id": r[1],
                        "driver_id": r[2],
                        "ride_id": r[3],
                        "status": r[4]
                    }
                    print(f"\n📝 Processing match ID: {match['id']}")
                    print(f"   User ID: {match['user_id']}")
                    print(f"   Driver ID: {match['driver_id']}")
                    print(f"   Ride ID: {match['ride_id']}")

                    # Find ride details (use ORM on RideRequest)
                    ride = None
                    if match['ride_id']:
                        ride = db.query(RideRequest).filter(RideRequest.id == match['ride_id']).first()

                    if not ride:
                        ride = db.query(RideRequest).filter(RideRequest.user_id == match['user_id']).order_by(RideRequest.created_at.desc()).first()

                    driver = db.query(DriverInfo).filter(DriverInfo.driver_id == match['driver_id']).first()

                    if not ride or not driver:
                        print(f"   ⚠️  Missing ride or driver info")
                        if not ride:
                            print(f"      Ride not found (ride_id: {match['ride_id']}, user_id: {match['user_id']})")
                        if not driver:
                            print(f"      Driver not found (driver_id: {match['driver_id']})")

                        # Mark match as failed to avoid infinite retry (use raw SQL update)
                        try:
                            db.execute(text("UPDATE matched_rides SET status = :s WHERE id = :id"), {"s": "failed", "id": match['id']})
                            db.commit()
                            print(f"   ❌ Marked match {match['id']} as failed - will not retry")
                        except Exception as e:
                            db.rollback()
                            print(f"   ❌ Failed to mark match as failed: {e}")
                        continue

                    # Ports (python clients) mapping
                    user_port = match['user_id']
                    driver_port = match['driver_id']

                    print(f"   🔌 User port: {user_port}, Driver port: {driver_port}")

                    # Notify orchestrator (best-effort)
                    try:
                        requests.post(
                            "http://localhost:8000/update_match/",
                            json={"user_id": match['user_id'], "driver_id": match['driver_id']},
                            timeout=2
                        )
                        print(f"   ✅ Orchestrator notified")
                    except Exception as e:
                        print(f"   ⚠️  Could not notify orchestrator: {e}")

                    # Notify user client
                    user_notified = False
                    is_web_user = False
                    try:
                        health_check = requests.get(f"http://localhost:{user_port}/status", timeout=0.5)
                        if health_check.status_code == 200:
                            # Python user client - POST assignment
                            try:
                                response = requests.post(
                                    f"http://localhost:{user_port}/ride/assigned",
                                    json={
                                        "ride_id": ride.id,
                                        "driver_id": match['driver_id'],
                                        "driver_name": f"Driver {match['driver_id']}",
                                        "driver_location": driver.current_location,
                                        "pickup_location": ride.source_location,
                                        "dropoff_location": ride.dest_location
                                    },
                                    timeout=2
                                )
                                if response.status_code == 200:
                                    print(f"   ✅ User client notified on port {user_port}")
                                    user_notified = True
                            except Exception as e:
                                print(f"   ⚠️  Could not notify user client on port {user_port}: {e}")
                    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                        # web user
                        is_web_user = True
                        print(f"   ℹ️  User {match['user_id']} is a web user (no port) - will poll for assignment")

                    if is_web_user:
                        user_notified = True  # DB presence suffices for web users

                    # Notify driver client
                    driver_notified = False
                    is_web_driver = False
                    try:
                        health_check = requests.get(f"http://localhost:{driver_port}/status", timeout=0.5)
                        if health_check.status_code == 200:
                            # Python driver client
                            for attempt in range(3):
                                try:
                                    response = requests.post(
                                        f"http://localhost:{driver_port}/ride/assigned",
                                        json={
                                            "ride_id": ride.id,
                                            "user_id": match['user_id'],
                                            "pickup_location": ride.source_location,
                                            "dropoff_location": ride.dest_location
                                        },
                                        timeout=5
                                    )
                                    if response.status_code == 200:
                                        print(f"   ✅ Driver client notified on port {driver_port}")
                                        driver_notified = True
                                        break
                                except Exception as e:
                                    if attempt == 2:
                                        print(f"   ⚠️  Could not notify Python driver on port {driver_port}: {e}")
                                    await asyncio.sleep(1)
                        else:
                            is_web_driver = True
                    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                        is_web_driver = True
                        print(f"   ℹ️  Driver {match['driver_id']} is a web driver (no port) - will poll for assignment")

                    if is_web_driver:
                        print(f"   ✅ Match stored - web driver {match['driver_id']} can poll for assignment")
                        driver_notified = True

                    # Now decide next steps based on notifications
                    if user_notified and driver_notified:
                        # If both are web clients, keep match. If both python clients, delete match row
                        if is_web_user or is_web_driver:
                            # keep match in DB (already present)
                            try:
                                db.commit()
                                print(f"   ✅ Match kept in DB for web polling (match id: {match['id']})")
                            except Exception as e:
                                db.rollback()
                                print(f"   ⚠️  Failed to commit after notifications: {e}")
                        else:
                            # both python clients -> delete the match row
                            try:
                                db.execute(text("DELETE FROM matched_rides WHERE id = :id"), {"id": match['id']})
                                db.commit()
                                print(f"   ✅ Match {match['id']} deleted from DB after notifications")
                            except Exception as e:
                                db.rollback()
                                print(f"   ⚠️  Failed to delete match {match['id']}: {e}")
                    elif not driver_notified:
                        print(f"   ❌ FAILED to notify driver {driver_port}")
                        # mark driver unavailable, requeue ride, delete match
                        try:
                            db.execute(text("UPDATE driver_info SET available = false WHERE driver_id = :did"), {"did": match['driver_id']})
                            db.execute(text("UPDATE ride_requests SET status = 'pending' WHERE id = :rid"), {"rid": ride.id})
                            db.execute(text("DELETE FROM matched_rides WHERE id = :id"), {"id": match['id']})
                            db.commit()
                            print(f"   🔄 Ride {ride.id} re-queued for another driver")
                        except Exception as e:
                            db.rollback()
                            print(f"   ⚠️  Failed to requeue ride after driver notification failure: {e}")
                        continue
                    elif not user_notified:
                        print(f"   ❌ FAILED to notify user {user_port}")
                        # For now keep match in DB for retry
                        try:
                            db.commit()
                        except:
                            db.rollback()
                        continue

            finally:
                db.close()

        except Exception as e:
            print(f"\n⚠️  Notifier loop error: {e}")
            import traceback
            traceback.print_exc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(notifier_loop())
    print("🔄 Notifier loop started (checking every 3 seconds).")
    yield
    task.cancel()
    print("🛑 Notifier loop stopped.")


app = FastAPI(title="Notifier Server", lifespan=lifespan)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def health():
    return {"message": "Notifier running on port 8002"}


@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get notification statistics"""
    try:
        cnt = db.execute(text("SELECT count(*) FROM matched_rides WHERE status = :s"), {"s": "pending_notification"}).scalar()
        return {"pending_notifications": int(cnt or 0), "note": "Matches are deleted after successful notification for Python clients"}
    except Exception as e:
        return {"pending_notifications": 0, "error": str(e)}


@app.get("/debug/matches")
def debug_matches(db: Session = Depends(get_db)):
    """Debug endpoint to see all matches in database"""
    try:
        rows = db.execute(text("SELECT id, user_id, driver_id, ride_id, status FROM matched_rides ORDER BY id DESC")).fetchall()
        matches = [{"id": r[0], "user_id": r[1], "driver_id": r[2], "ride_id": r[3], "status": r[4]} for r in rows]
        return {"count": len(matches), "matches": matches}
    except Exception as e:
        return {"count": 0, "matches": [], "error": str(e)}


@app.get("/debug/active-clients")
def check_active_clients(db: Session = Depends(get_db)):
    """Check which clients (users and drivers) are actually running"""
    results = {"drivers": [], "users": []}

    # Check drivers
    drivers = db.query(DriverInfo).all()
    for driver in drivers:
        port = driver.driver_id
        try:
            resp = requests.get(f"http://localhost:{port}/status", timeout=1)
            results["drivers"].append({
                "driver_id": driver.driver_id,
                "port": port,
                "online": True,
                "available": resp.json().get("is_available", False)
            })
        except:
            results["drivers"].append({
                "driver_id": driver.driver_id,
                "port": port,
                "online": False,
                "available": False
            })

    # Check users from recent rides
    rides = db.query(RideRequest).limit(10).all()
    checked_users = set()
    for ride in rides:
        if ride.user_id not in checked_users:
            checked_users.add(ride.user_id)
            port = ride.user_id
            try:
                resp = requests.get(f"http://localhost:{port}/status", timeout=1)
                results["users"].append({
                    "user_id": ride.user_id,
                    "port": port,
                    "online": True
                })
            except:
                results["users"].append({
                    "user_id": ride.user_id,
                    "port": port,
                    "online": False
                })

    return results


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("📢 Mini Uber Notifier Service")
    print("="*60)
    print("   Port: 8002")
    print("   Checking for matches every 3 seconds")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="warning")
