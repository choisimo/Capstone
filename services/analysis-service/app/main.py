from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import uvicorn
from app.db import get_db, engine, Base
from app.routers import sentiment, trends, reports, models as ml_models
from app.config import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Analysis Service starting up...")
    yield
    logger.info("Analysis Service shutting down...")


app = FastAPI(
    title="Analysis Service",
    description="Microservice for sentiment analysis, trend analysis, and reporting",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

app.include_router(sentiment.router, prefix="/api/v1/sentiment", tags=["sentiment"])
app.include_router(trends.router, prefix="/api/v1/trends", tags=["trends"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(ml_models.router, prefix="/api/v1/models", tags=["ml-models"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "analysis-service"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG
    )