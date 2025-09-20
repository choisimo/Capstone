from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SentimentAnalysisRequest(BaseModel):
    text: str = Field(..., description="Text to analyze")
    content_id: Optional[str] = Field(None, description="Unique identifier for the content")


class SentimentAnalysisResponse(BaseModel):
    content_id: str
    sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="Sentiment score between -1 and 1")
    sentiment_label: str = Field(..., description="Sentiment label: positive, negative, neutral")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    model_version: str
    analysis_id: int


class BatchSentimentRequest(BaseModel):
    texts: List[SentimentAnalysisRequest]


class BatchSentimentResponse(BaseModel):
    results: List[SentimentAnalysisResponse]
    total_processed: int
    success_count: int
    error_count: int


class TrendAnalysisRequest(BaseModel):
    period: str = Field(..., description="Analysis period: daily, weekly, monthly")
    entity: Optional[str] = Field(None, description="Specific entity to analyze")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class TrendItem(BaseModel):
    date: datetime
    sentiment_score: float
    volume: int
    keywords: List[str]


class TrendAnalysisResponse(BaseModel):
    period: str
    entity: str
    trend_direction: str  # increasing, decreasing, stable
    trend_strength: float
    data_points: List[TrendItem]
    summary: str


class ReportRequest(BaseModel):
    report_type: str = Field(..., description="Type of report: sentiment, trend, summary")
    title: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ReportResponse(BaseModel):
    report_id: int
    title: str
    report_type: str
    content: Dict[str, Any]
    created_at: datetime
    download_url: Optional[str] = None


class MLModelRequest(BaseModel):
    name: str
    model_type: str = Field(..., description="Type of model: sentiment, classification")
    file_path: str
    metrics: Dict[str, Any] = Field(default_factory=dict)


class MLModelResponse(BaseModel):
    model_id: int
    name: str
    version: str
    model_type: str
    is_active: bool
    metrics: Dict[str, Any]
    created_at: datetime


class ModelTrainingRequest(BaseModel):
    model_name: str
    training_data_path: str
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    validation_split: float = Field(0.2, ge=0.1, le=0.5)


class ModelTrainingResponse(BaseModel):
    job_id: str
    status: str
    estimated_completion: Optional[datetime] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime
    database_connected: bool
    models_loaded: int