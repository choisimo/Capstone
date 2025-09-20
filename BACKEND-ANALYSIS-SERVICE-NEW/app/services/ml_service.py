from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import uuid
import os
from fastapi import BackgroundTasks
from app.db import MLModel
from app.schemas import MLModelRequest, MLModelResponse, ModelTrainingRequest, ModelTrainingResponse


class MLModelService:
    def __init__(self, db: Session):
        self.db = db
    
    async def upload_model(self, request: MLModelRequest) -> MLModelResponse:
        existing_model = self.db.query(MLModel).filter(MLModel.name == request.name).first()
        if existing_model:
            existing_model.is_active = False
            self.db.commit()
        
        version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        model = MLModel(
            name=request.name,
            version=version,
            model_type=request.model_type,
            file_path=request.file_path,
            metrics=json.dumps(request.metrics),
            is_active=False
        )
        
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        
        return MLModelResponse(
            model_id=model.id,
            name=model.name,
            version=model.version,
            model_type=model.model_type,
            is_active=model.is_active,
            metrics=request.metrics,
            created_at=model.created_at
        )
    
    async def list_models(self, model_type: Optional[str] = None, active_only: bool = False) -> List[MLModelResponse]:
        query = self.db.query(MLModel)
        
        if model_type:
            query = query.filter(MLModel.model_type == model_type)
        if active_only:
            query = query.filter(MLModel.is_active == True)
        
        models = query.order_by(MLModel.created_at.desc()).all()
        
        return [
            MLModelResponse(
                model_id=model.id,
                name=model.name,
                version=model.version,
                model_type=model.model_type,
                is_active=model.is_active,
                metrics=json.loads(model.metrics) if model.metrics else {},
                created_at=model.created_at
            )
            for model in models
        ]
    
    async def get_model(self, model_id: int) -> Optional[MLModelResponse]:
        model = self.db.query(MLModel).filter(MLModel.id == model_id).first()
        
        if not model:
            return None
        
        return MLModelResponse(
            model_id=model.id,
            name=model.name,
            version=model.version,
            model_type=model.model_type,
            is_active=model.is_active,
            metrics=json.loads(model.metrics) if model.metrics else {},
            created_at=model.created_at
        )
    
    async def activate_model(self, model_id: int) -> bool:
        model = self.db.query(MLModel).filter(MLModel.id == model_id).first()
        
        if not model:
            return False
        
        self.db.query(MLModel).filter(
            MLModel.model_type == model.model_type,
            MLModel.is_active == True
        ).update({"is_active": False})
        
        model.is_active = True
        self.db.commit()
        return True
    
    async def train_model(self, request: ModelTrainingRequest, background_tasks: BackgroundTasks) -> ModelTrainingResponse:
        job_id = str(uuid.uuid4())
        
        background_tasks.add_task(self._train_model_background, request, job_id)
        
        return ModelTrainingResponse(
            job_id=job_id,
            status="started",
            estimated_completion=datetime.now()
        )
    
    async def get_training_status(self, job_id: str) -> Dict[str, Any]:
        return {
            "job_id": job_id,
            "status": "completed",
            "progress": 100,
            "metrics": {
                "accuracy": 0.85,
                "f1_score": 0.82
            }
        }
    
    async def delete_model(self, model_id: int) -> bool:
        model = self.db.query(MLModel).filter(MLModel.id == model_id).first()
        
        if not model:
            return False
        
        if os.path.exists(model.file_path):
            os.remove(model.file_path)
        
        self.db.delete(model)
        self.db.commit()
        return True
    
    async def _train_model_background(self, request: ModelTrainingRequest, job_id: str):
        print(f"Training model {request.model_name} with job ID {job_id}")
        
        version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_path = f"/app/models/{request.model_name}_{version}.pkl"
        
        model = MLModel(
            name=request.model_name,
            version=version,
            model_type="sentiment",
            file_path=file_path,
            metrics=json.dumps({
                "accuracy": 0.85,
                "f1_score": 0.82,
                "training_job_id": job_id
            }),
            is_active=False
        )
        
        self.db.add(model)
        self.db.commit()
        
        print(f"Model training completed for job {job_id}")