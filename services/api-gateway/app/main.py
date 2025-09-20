from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import httpx
from contextlib import asynccontextmanager

from app.config import settings
from app.routers import analysis, collector, absa, alerts

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.http_client = httpx.AsyncClient(timeout=30.0)
    yield
    # Shutdown
    await app.state.http_client.aclose()

# Create FastAPI app with lifespan
app = FastAPI(
    title="Pension Sentiment Analysis - API Gateway",
    description="Central API Gateway for all microservices",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for API Gateway"""
    services_status = {}
    
    # Check all microservices health
    services = {
        "analysis": settings.ANALYSIS_SERVICE_URL,
        "collector": settings.COLLECTOR_SERVICE_URL,
        "absa": settings.ABSA_SERVICE_URL,
        "alert": settings.ALERT_SERVICE_URL
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service, url in services.items():
            try:
                response = await client.get(f"{url}/health")
                services_status[service] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds()
                }
            except Exception as e:
                services_status[service] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
    
    overall_status = "healthy" if all(
        s["status"] == "healthy" for s in services_status.values()
    ) else "degraded"
    
    return {
        "status": overall_status,
        "services": services_status,
        "gateway_version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Pension Sentiment Analysis API Gateway",
        "version": "1.0.0",
        "services": {
            "analysis": "/api/v1/analysis",
            "collector": "/api/v1/collector", 
            "absa": "/api/v1/absa",
            "alerts": "/api/v1/alerts"
        },
        "docs": "/docs",
        "health": "/health"
    }

# Include service routers
app.include_router(
    analysis.router,
    prefix="/api/v1/analysis",
    tags=["Analysis Service"]
)

app.include_router(
    collector.router,
    prefix="/api/v1/collector",
    tags=["Collector Service"]
)

app.include_router(
    absa.router,
    prefix="/api/v1/absa", 
    tags=["ABSA Service"]
)

app.include_router(
    alerts.router,
    prefix="/api/v1/alerts",
    tags=["Alert Service"]
)

# Global exception handler
@app.exception_handler(httpx.TimeoutException)
async def timeout_handler(request, exc):
    return JSONResponse(
        status_code=504,
        content={"detail": "Service timeout - please try again later"}
    )

@app.exception_handler(httpx.ConnectError)
async def connect_error_handler(request, exc):
    return JSONResponse(
        status_code=503,
        content={"detail": "Service temporarily unavailable"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )