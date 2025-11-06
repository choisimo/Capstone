"""
API 의존성 관리
FastAPI Dependency Injection
"""
from typing import Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
import os
import logging

# 시스템 임포트
import sys
sys.path.append('..')
from hybrid_crawler_main import HybridCrawlerSystem

logger = logging.getLogger(__name__)

# API 키 보안
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# 글로벌 시스템 인스턴스
_crawler_system: Optional[HybridCrawlerSystem] = None


async def get_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    API 키 검증
    
    Args:
        api_key: 헤더에서 추출한 API 키
    
    Returns:
        검증된 API 키
    
    Raises:
        HTTPException: 401 Unauthorized if invalid
    """
    valid_api_key = os.getenv("API_KEY", "default-api-key-for-development")
    
    if not api_key or api_key != valid_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key


async def get_crawler_system() -> HybridCrawlerSystem:
    """
    크롤러 시스템 인스턴스 반환
    
    Returns:
        HybridCrawlerSystem 인스턴스
    """
    global _crawler_system
    
    if _crawler_system is None:
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gemini API key not configured"
            )
        
        _crawler_system = HybridCrawlerSystem(gemini_api_key=gemini_api_key)
        await _crawler_system.start()
        logger.info("Crawler system initialized and started")
    
    return _crawler_system


async def get_authenticated_system(
    api_key: str = Depends(get_api_key),
    system: HybridCrawlerSystem = Depends(get_crawler_system)
) -> HybridCrawlerSystem:
    """
    인증된 시스템 접근
    
    Args:
        api_key: 검증된 API 키
        system: 크롤러 시스템
    
    Returns:
        인증된 시스템 인스턴스
    """
    return system


# 선택적 인증 (일부 엔드포인트용)
async def get_optional_auth_system(
    api_key: Optional[str] = Security(api_key_header),
    system: HybridCrawlerSystem = Depends(get_crawler_system)
) -> HybridCrawlerSystem:
    """
    선택적 인증 시스템 접근 (헬스체크 등)
    
    Args:
        api_key: 선택적 API 키
        system: 크롤러 시스템
    
    Returns:
        시스템 인스턴스
    """
    # API 키가 제공된 경우만 검증
    if api_key:
        valid_api_key = os.getenv("API_KEY", "default-api-key-for-development")
        if api_key != valid_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key"
            )
    
    return system


# 데이터베이스 의존성 (향후 Phase 3에서 구현)
async def get_db():
    """데이터베이스 세션 반환"""
    # TODO: Phase 3 - Task 015에서 구현
    pass


# 캐시 의존성 (향후 Phase 3에서 구현)
async def get_cache():
    """캐시 클라이언트 반환"""
    # TODO: Phase 3 - Task 016에서 구현
    pass


# 메시지 큐 의존성 (향후 Phase 3에서 구현)
async def get_message_queue():
    """메시지 큐 클라이언트 반환"""
    # TODO: Phase 3 - Task 017에서 구현
    pass
