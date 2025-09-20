from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.db import engine, Base
from app.routers import alerts, rules, notifications
from app.config import settings

app = FastAPI(
    title="Pension Sentiment Alert Service",
    description="Notification and alerting system for pension sentiment analysis",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alerts.router, prefix="/alerts", tags=["Alert Management"])
app.include_router(rules.router, prefix="/rules", tags=["Alert Rules"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "alert-service"}

@app.get("/")
async def root():
    return {
        "service": "Pension Sentiment Alert Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "alerts": "/alerts - Alert management",
            "rules": "/rules - Alert rule configuration",
            "notifications": "/notifications - Notification handling",
            "health": "/health - Health check",
            "docs": "/docs - API documentation"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)