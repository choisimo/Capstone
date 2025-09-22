"""
속성 추출 라우터

텍스트에서 분석할 속성(aspects)을 추출하는 API 엔드포인트입니다.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.db import get_db, AspectModel
import json

router = APIRouter()


@router.post("/extract")
async def extract_aspects(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    텍스트에서 속성 추출
    
    주어진 텍스트에서 분석 대상 속성을 추출합니다.
    
    Args:
        request: {"text": str} 형태의 요청
        db: 데이터베이스 세션
        
    Returns:
        추출된 속성 리스트와 신뢰도
    """
    text = request.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    # 활성화된 속성 모델 조회
    active_aspects = db.query(AspectModel).filter(
        AspectModel.is_active == 1
    ).all()
    
    # 간단한 키워드 매칭 방식 (실제로는 ML 모델 사용)
    extracted_aspects = []
    
    for aspect_model in active_aspects:
        keywords = aspect_model.keywords or []
        # 텍스트에 키워드가 포함되어 있는지 확인
        for keyword in keywords:
            if keyword.lower() in text.lower():
                extracted_aspects.append({
                    "aspect": aspect_model.name,
                    "confidence": 0.85,  # 임시 신뢰도
                    "keywords_found": [keyword]
                })
                break
    
    # 기본 속성 추가 (키워드 매칭 실패 시)
    if not extracted_aspects:
        default_aspects = ["수익률", "안정성", "관리비용", "가입조건"]
        for aspect in default_aspects:
            if aspect in text or len(text) > 20:  # 텍스트가 충분히 길면
                extracted_aspects.append({
                    "aspect": aspect,
                    "confidence": 0.7,
                    "keywords_found": []
                })
    
    return {
        "text": text[:200],  # 텍스트 미리보기
        "aspects": extracted_aspects,
        "total_aspects": len(extracted_aspects),
        "model_version": "v1.0.0"
    }


@router.get("/list")
async def list_aspects(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    사용 가능한 속성 목록 조회
    
    Returns:
        활성화된 속성 모델 목록
    """
    aspects = db.query(AspectModel).filter(
        AspectModel.is_active == 1
    ).all()
    
    return {
        "aspects": [
            {
                "id": aspect.id,
                "name": aspect.name,
                "description": aspect.description,
                "keywords": aspect.keywords,
                "model_version": aspect.model_version
            }
            for aspect in aspects
        ],
        "total": len(aspects)
    }


@router.post("/create")
async def create_aspect(
    aspect_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    새로운 속성 모델 생성
    
    Args:
        aspect_data: 속성 정보
        db: 데이터베이스 세션
        
    Returns:
        생성된 속성 정보
    """
    # 중복 확인
    existing = db.query(AspectModel).filter(
        AspectModel.name == aspect_data.get("name")
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Aspect already exists")
    
    # 새 속성 생성
    new_aspect = AspectModel(
        name=aspect_data.get("name"),
        description=aspect_data.get("description", ""),
        keywords=aspect_data.get("keywords", []),
        model_version=aspect_data.get("model_version", "v1.0.0")
    )
    
    db.add(new_aspect)
    db.commit()
    db.refresh(new_aspect)
    
    return {
        "id": new_aspect.id,
        "name": new_aspect.name,
        "description": new_aspect.description,
        "keywords": new_aspect.keywords,
        "created_at": new_aspect.created_at.isoformat() if new_aspect.created_at else None
    }
