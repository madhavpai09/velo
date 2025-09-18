from fastapi import FastAPI
from api.routes import router
from database.connection import create_tables

app = FastAPI(title="Mini-Uber", version="1.0.0")

# Include API routes
app.include_router(router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Create database tables on startup"""
    create_tables()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)