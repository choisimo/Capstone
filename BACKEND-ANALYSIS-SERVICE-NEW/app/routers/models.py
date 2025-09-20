from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app.schemas import (
    MLModelRequest, 
    MLModelResponse, 
    ModelTrainingRequest, 
    ModelTrainingResponse
)
from app.services.ml_service import MLModelService

router = APIRouter()


@router.post("/upload", response_model=MLModelResponse)
async def upload_model(
    request: MLModelRequest,
    db: Session = Depends(get_db)
):
    service = MLModelService(db)
    result = await service.upload_model(request)
    return result


@router.get("/", response_model=List[MLModelResponse])
async def list_models(
    model_type: Optional[str] = None,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    service = MLModelService(db)
    models = await service.list_models(model_type, active_only)
    return models


@router.get("/{model_id}", response_model=MLModelResponse)
async def get_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    service = MLModelService(db)
    model = await service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.put("/{model_id}/activate")
async def activate_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    service = MLModelService(db)
    success = await service.activate_model(model_id)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"message": "Model activated successfully"}


@router.post("/train", response_model=ModelTrainingResponse)
async def train_model(
    request: ModelTrainingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    service = MLModelService(db)
    result = await service.train_model(request, background_tasks)
    return result


@router.get("/training/{job_id}")
async def get_training_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    service = MLModelService(db)
    status = await service.get_training_status(job_id)
    return status


@router.delete("/{model_id}")
async def delete_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    service = MLModelService(db)
    success = await service.delete_model(model_id)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"message": "Model deleted successfully"}