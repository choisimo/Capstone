"""
ABSA 모델 관리 라우터

ABSA 모델의 생성, 조회, 업데이트, 삭제를 관리하는 API 엔드포인트입니다.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.db import get_db, AspectModel
from datetime import datetime
from pydantic import BaseModel, Field

# Optional: use shared pagination schema if available
try:
    from shared.schemas import PaginationMeta as SharedPaginationMeta  # type: ignore
except Exception:
    SharedPaginationMeta = None  # Fallback defined below


class PaginationMeta(BaseModel):
    total: int = Field(..., ge=0)
    limit: int = Field(..., ge=1)
    offset: int = Field(..., ge=0)


# If shared PaginationMeta exists, alias to it to keep one definition
if SharedPaginationMeta is not None:
    PaginationMeta = SharedPaginationMeta  # type: ignore


class ModelItem(BaseModel):
    id: str
    name: str
    description: str | None = None
    model_version: str | None = None
    is_active: int | bool
    created_at: str | None = None


class ModelListResponse(BaseModel):
    models: List[ModelItem]
    total: int
    skip: int
    limit: int
    pagination: PaginationMeta


class ModelDetailResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    keywords: List[str] | None = None
    model_version: str | None = None
    is_active: int | bool
    created_at: str | None = None
    updated_at: str | None = None


class ModelUpdateResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    keywords: List[str] | None = None
    model_version: str | None = None
    is_active: int | bool
    updated_at: str | None = None


class DeleteResponse(BaseModel):
    message: str
    deleted_id: str


class InitializeResponse(BaseModel):
    created: List[str]
    skipped: List[str]
    total_created: int
    total_skipped: int


router = APIRouter()


@router.get("/", response_model=ModelListResponse)
async def list_models(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
) -> ModelListResponse:
    """
    ABSA 모델 목록 조회
    
    Args:
        skip: 건너뛸 개수
        limit: 조회할 최대 개수
        db: 데이터베이스 세션
        
    Returns:
        모델 목록과 메타데이터
    """
    models = db.query(AspectModel).offset(skip).limit(limit).all()
    total = db.query(AspectModel).count()

    items = [
        ModelItem(
            id=model.id,
            name=model.name,
            description=model.description,
            model_version=model.model_version,
            is_active=model.is_active,
            created_at=model.created_at.isoformat() if model.created_at else None,
        )
        for model in models
    ]

    return ModelListResponse(
        models=items,
        total=total,
        skip=skip,
        limit=limit,
        pagination=PaginationMeta(total=total, limit=limit, offset=skip),
    )


@router.get("/{model_id}", response_model=ModelDetailResponse)
async def get_model(
    model_id: str,
    db: Session = Depends(get_db)
) -> ModelDetailResponse:
    """
    특정 ABSA 모델 상세 조회
    
    Args:
        model_id: 모델 ID
        db: 데이터베이스 세션
        
    Returns:
        모델 상세 정보
    """
    model = db.query(AspectModel).filter(AspectModel.id == model_id).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return ModelDetailResponse(
        id=model.id,
        name=model.name,
        description=model.description,
        keywords=model.keywords,
        model_version=model.model_version,
        is_active=model.is_active,
        created_at=model.created_at.isoformat() if model.created_at else None,
        updated_at=model.updated_at.isoformat() if model.updated_at else None,
    )


@router.put("/{model_id}", response_model=ModelUpdateResponse)
async def update_model(
    model_id: str,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> ModelUpdateResponse:
    """
    ABSA 모델 업데이트
    
    Args:
        model_id: 모델 ID
        update_data: 업데이트할 데이터
        db: 데이터베이스 세션
        
    Returns:
        업데이트된 모델 정보
    """
    model = db.query(AspectModel).filter(AspectModel.id == model_id).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # 업데이트 가능한 필드
    updateable_fields = ["name", "description", "keywords", "model_version", "is_active"]
    
    for field in updateable_fields:
        if field in update_data:
            setattr(model, field, update_data[field])
    
    db.commit()
    db.refresh(model)
    
    return ModelUpdateResponse(
        id=model.id,
        name=model.name,
        description=model.description,
        keywords=model.keywords,
        model_version=model.model_version,
        is_active=model.is_active,
        updated_at=model.updated_at.isoformat() if model.updated_at else None,
    )


@router.delete("/{model_id}", response_model=DeleteResponse)
async def delete_model(
    model_id: str,
    db: Session = Depends(get_db)
) -> DeleteResponse:
    """
    ABSA 모델 삭제
    
    Args:
        model_id: 모델 ID
        db: 데이터베이스 세션
        
    Returns:
        삭제 결과
    """
    model = db.query(AspectModel).filter(AspectModel.id == model_id).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model_name = model.name
    db.delete(model)
    db.commit()
    
    return DeleteResponse(
        message=f"Model '{model_name}' deleted successfully",
        deleted_id=model_id,
    )


@router.post("/initialize", response_model=InitializeResponse)
async def initialize_default_models(
    db: Session = Depends(get_db)
) -> InitializeResponse:
    """
    기본 ABSA 모델 초기화
    
    연금 관련 기본 속성 모델을 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        
    Returns:
        초기화 결과
    """
    default_aspects = [
        {
            "name": "수익률",
            "description": "투자 수익률 및 수익성 관련 속성",
            "keywords": ["수익", "이익", "수익률", "수익성", "투자수익", "운용수익"]
        },
        {
            "name": "안정성",
            "description": "연금 운용의 안정성 및 신뢰성",
            "keywords": ["안정", "신뢰", "보장", "안전", "리스크", "위험"]
        },
        {
            "name": "관리비용",
            "description": "관리 수수료 및 비용 관련",
            "keywords": ["수수료", "비용", "관리비", "운용비", "비용부담", "수수료율"]
        },
        {
            "name": "가입조건",
            "description": "가입 자격 및 조건",
            "keywords": ["가입", "자격", "조건", "요건", "신청", "가입절차"]
        },
        {
            "name": "서비스",
            "description": "고객 서비스 및 지원",
            "keywords": ["서비스", "상담", "지원", "고객", "응대", "안내"]
        }
    ]
    
    created_models = []
    skipped_models = []
    
    for aspect_data in default_aspects:
        # 중복 확인
        existing = db.query(AspectModel).filter(
            AspectModel.name == aspect_data["name"]
        ).first()
        
        if existing:
            skipped_models.append(aspect_data["name"])
            continue
        
        # 새 모델 생성
        model = AspectModel(
            name=aspect_data["name"],
            description=aspect_data["description"],
            keywords=aspect_data["keywords"],
            model_version="v1.0.0",
            is_active=1
        )
        
        db.add(model)
        created_models.append(aspect_data["name"])
    
    db.commit()
    
    return InitializeResponse(
        created=created_models,
        skipped=skipped_models,
        total_created=len(created_models),
        total_skipped=len(skipped_models),
    )
