from fastapi import FastAPI, Request
import requests

app = FastAPI(title="Notifier Server")

@app.get("/")
def health():
    return {"message": "Notifier running on port 8002"}

@app.post("/notify_match/")
async def notify_match(req: Request):
    data = await req.json()
    user_id = data.get("user_id")
    driver_id = data.get("driver_id")

    # Notify orchestrator (port 8000)
    requests.post("http://localhost:8000/update_match/", json={
        "user_id": user_id,
        "driver_id": driver_id
    })

    return {"message": "Notified orchestrator", "user_id": user_id, "driver_id": driver_id}

