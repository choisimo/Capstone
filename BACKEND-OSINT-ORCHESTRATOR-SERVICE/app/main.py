import uvicorn
from fastapi import FastAPI
from app.config import settings

app = FastAPI(
    title="OSINT Task Orchestrator Service",
    description="Orchestrates OSINT tasks with priority-based queue management and worker coordination",
    version="1.0.0"
)

# from app.routers import tasks
# app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "osint-task-orchestrator"}

@app.get("/metrics")
async def get_metrics():
    return {
        "service": "osint-task-orchestrator",
        "queue_stats": {"total_tasks": 0, "pending_tasks": 0},
        "active_workers": 0,
        "total_workers": 0
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)