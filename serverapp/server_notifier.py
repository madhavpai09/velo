from fastapi import FastAPI, Request
import requests

app = FastAPI(title="Notifier Server")

@app.get("/")
def health():
    return {"message": "Notifier running on port 8002"}

@app.post("/notify_match/")
async def notify_match(req: Request):
    """Notify orchestrator and clients about the match"""
    data = await req.json()
    user_id = data.get("user_id")
    driver_id = data.get("driver_id")
    
    print(f"📢 Notifying match: User {user_id} ↔ Driver {driver_id}")

    # 1. Notify orchestrator (port 8000)
    try:
        requests.post("http://localhost:8000/update_match/", json={
            "user_id": user_id,
            "driver_id": driver_id
        }, timeout=2)
        print(f"   ✅ Orchestrator notified")
    except Exception as e:
        print(f"   ⚠️  Could not notify orchestrator: {e}")

    # 2. Notify user client (assumes user is listening on port based on user_id)
    # If user_id is the port number (e.g., 6000), use it directly
    user_port = user_id if user_id >= 6000 else 6000
    try:
        response = requests.post(
            f"http://localhost:{user_port}/match_update",
            json={
                "driver_id": driver_id,
                "driver_name": f"Driver {driver_id}",
                "source_location": data.get("source_location"),
                "dest_location": data.get("dest_location"),
                "driver_location": data.get("driver_location")
            },
            timeout=2
        )
        print(f"   ✅ User client notified on port {user_port}")
    except Exception as e:
        print(f"   ⚠️  Could not notify user client on port {user_port}: {e}")

    # 3. Notify driver client (assumes driver is listening on port based on driver_id)
    # If driver_id is the port number (e.g., 9000), use it directly
    driver_port = driver_id if driver_id >= 9000 else 9000
    try:
        response = requests.post(
            f"http://localhost:{driver_port}/match_update",
            json={
                "user_id": user_id,
                "user_name": f"User {user_id}",
                "source_location": data.get("source_location"),
                "dest_location": data.get("dest_location")
            },
            timeout=2
        )
        print(f"   ✅ Driver client notified on port {driver_port}")
    except Exception as e:
        print(f"   ⚠️  Could not notify driver client on port {driver_port}: {e}")

    return {
        "message": "Notifications sent",
        "user_id": user_id,
        "driver_id": driver_id
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)