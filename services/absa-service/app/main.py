from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.db import engine, Base
from app.routers import aspects, analysis, models
from app.config import settings

app = FastAPI(
    title="Pension Sentiment ABSA Service",
    description="Aspect-Based Sentiment Analysis for pension content",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(aspects.router, prefix="/aspects", tags=["Aspect Extraction"])
app.include_router(analysis.router, prefix="/analysis", tags=["ABSA Analysis"])
app.include_router(models.router, prefix="/models", tags=["ABSA Models"])

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "absa-service"}

@app.get("/")
async def root():
    return {
        "service": "Pension Sentiment ABSA Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "aspects": "/aspects - Aspect extraction operations",
            "analysis": "/analysis - ABSA analysis operations",
            "models": "/models - ABSA model management",
            "health": "/health - Health check",
            "docs": "/docs - API documentation"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)