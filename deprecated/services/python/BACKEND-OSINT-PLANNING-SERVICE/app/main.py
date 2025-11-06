import uvicorn
from fastapi import FastAPI

from app.config import settings
from shared.eureka_client import create_manager_from_settings

app = FastAPI(
    title="OSINT Planning Service",
    description="AI-powered OSINT collection planning with keyword expansion and source recommendation",
    version="1.0.0"
)

eureka_manager = create_manager_from_settings(
    enabled=settings.EUREKA_ENABLED,
    service_urls=settings.EUREKA_SERVICE_URLS,
    app_name=settings.EUREKA_APP_NAME,
    instance_port=settings.PORT,
    instance_host=settings.EUREKA_INSTANCE_HOST,
    instance_ip=settings.EUREKA_INSTANCE_IP,
    metadata=settings.EUREKA_METADATA,
)

from app.routers import keywords
# Router already defines prefix=/api/v1/plans; include without extra prefix to avoid duplication
app.include_router(keywords.router, tags=["plans"])


@app.on_event("startup")
async def on_startup() -> None:
    await eureka_manager.register()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await eureka_manager.deregister()

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
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)