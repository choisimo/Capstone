import uvicorn
from app.config import settings

class FastAPI:
    def __init__(self, title="", description="", version=""):
        self.title = title
        self.description = description
        self.version = version
        self.routes = []
    
    def include_router(self, router, prefix="", tags=None):
        pass
    
    def get(self, path: str):
        def decorator(func):
            return func
        return decorator

app = FastAPI(
    title="OSINT Task Orchestrator Service",
    description="Orchestrates OSINT tasks with priority-based queue management and worker coordination",
    version="1.0.0"
)

from app.routers import tasks

app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "osint-task-orchestrator"}

@app.get("/metrics")
async def get_metrics():
    from app.services.orchestrator_service import orchestrator
    stats = await orchestrator.get_queue_stats()
    return {
        "service": "osint-task-orchestrator",
        "queue_stats": stats,
        "active_workers": len([w for w in orchestrator.workers.values() if w.status == "active"]),
        "total_workers": len(orchestrator.workers)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)