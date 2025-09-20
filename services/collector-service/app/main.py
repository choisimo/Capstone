from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  
from fastapi.responses import JSONResponse
import asyncio
import uvicorn
from app.db import engine, Base, get_db
from app.routers import sources, collections, feeds
from app.config import settings

app = FastAPI(
    title="Pension Sentiment Collector Service",
    description="Web scraping and RSS feed collection for pension sentiment data",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sources.router, prefix="/sources", tags=["Data Sources"])
app.include_router(collections.router, prefix="/collections", tags=["Data Collection"])
app.include_router(feeds.router, prefix="/feeds", tags=["RSS Feeds"])

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "collector-service"}

@app.get("/")
async def root():
    return {
        "service": "Pension Sentiment Collector Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "sources": "/sources - Manage data sources",
            "collections": "/collections - Data collection operations",
            "feeds": "/feeds - RSS feed management",
            "health": "/health - Health check",
            "docs": "/docs - API documentation"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)