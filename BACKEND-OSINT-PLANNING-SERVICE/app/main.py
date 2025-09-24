import uvicorn
from fastapi import FastAPI
from app.config import settings

app = FastAPI(
    title="OSINT Planning Service",
    description="AI-powered OSINT collection planning with keyword expansion and source recommendation",
    version="1.0.0"
)

# from app.routers import keywords
# app.include_router(keywords.router, prefix="/api/v1/plans", tags=["plans"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "osint-planning-service"}

@app.get("/metrics")
async def get_metrics():
    return {
        "service": "osint-planning-service",
        "total_plans": 0,
        "active_plans": 0,
        "total_executions": 0,
        "running_executions": 0
    }

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8006))
    uvicorn.run(app, host="0.0.0.0", port=port)