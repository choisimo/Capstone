"""
소스 관리 서비스

데이터 수집 소스를 관리하는 서비스입니다.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import hashlib


class SourceService:
    """
    데이터 소스 관리 서비스 클래스
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def list_sources(self, source_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        등록된 데이터 소스 목록 조회
        
        Args:
            source_type: 소스 타입 필터 (rss, web, api 등)
            
        Returns:
            소스 목록
        """
        # 실제 국민연금 관련 소스
        sources = [
            {
                "id": 1,
                "name": "국민연금공단 공식",
                "source_type": "web",
                "url": "https://www.nps.or.kr",
                "is_active": True,
                "collection_frequency": 3600,  # 1시간마다
                "created_at": datetime.now(),
                "last_collected": None,
                "updated_at": None,
                "metadata_json": {"official": True}
            },
            {
                "id": 2,
                "name": "보건복지부",
                "source_type": "web",
                "url": "https://www.mohw.go.kr",
                "is_active": True,
                "collection_frequency": 3600,
                "created_at": datetime.now(),
                "last_collected": None,
                "updated_at": None,
                "metadata_json": {"official": True}
            },
            {
                "id": 3,
                "name": "국민연금공단 RSS",
                "source_type": "rss",
                "url": "https://www.nps.or.kr/jsppage/cyber_pr/news/rss.jsp",
                "is_active": True,
                "collection_frequency": 1800,  # 30분마다
                "created_at": datetime.now(),
                "last_collected": None,
                "updated_at": None,
                "metadata_json": {"feed_type": "rss"}
            },
            {
                "id": 4,
                "name": "보건복지부 RSS",
                "source_type": "rss",
                "url": "https://www.mohw.go.kr/rss/news.xml",
                "is_active": True,
                "collection_frequency": 1800,
                "created_at": datetime.now(),
                "last_collected": None,
                "updated_at": None,
                "metadata_json": {"feed_type": "rss"}
            },
            {
                "id": 5,
                "name": "네이버 뉴스 검색",
                "source_type": "web",
                "url": "https://search.naver.com/search.naver?where=news&query=국민연금",
                "is_active": True,
                "collection_frequency": 7200,  # 2시간마다
                "created_at": datetime.now(),
                "last_collected": None,
                "updated_at": None,
                "metadata_json": {"search_query": "국민연금"}
            },
            {
                "id": 6,
                "name": "다음 뉴스 검색",
                "source_type": "web",
                "url": "https://search.daum.net/search?w=news&q=국민연금",
                "is_active": True,
                "collection_frequency": 7200,
                "created_at": datetime.now(),
                "last_collected": None,
                "updated_at": None,
                "metadata_json": {"search_query": "국민연금"}
            }
        ]
        
        if source_type:
            sources = [s for s in sources if s["source_type"] == source_type]
        
        return sources
    
    def get_sources(self, skip: int = 0, limit: int = 100, active_only: bool = None) -> List[Dict[str, Any]]:
        """
        데이터 소스 목록 조회 (페이징 지원)
        
        Args:
            skip: 건너뛸 항목 수
            limit: 최대 반환 항목 수
            active_only: True면 활성 소스만
            
        Returns:
            소스 목록
        """
        sources = self.list_sources()
        
        if active_only is not None:
            sources = [s for s in sources if s["is_active"] == active_only]
        
        return sources[skip:skip + limit]
    
    def get_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        """
        특정 소스 상세 조회
        
        Args:
            source_id: 소스 ID
            
        Returns:
            소스 정보
        """
        sources = self.list_sources()
        for source in sources:
            if source["id"] == source_id:
                return source
        return None
    
    def create_source(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        새 데이터 소스 등록
        
        Args:
            source_data: 소스 정보
            
        Returns:
            생성된 소스 정보
        """
        new_source = {
            "id": source_data.get("id", str(uuid.uuid4())),
            "name": source_data.get("name"),
            "type": source_data.get("type", "web"),
            "url": source_data.get("url"),
            "config": source_data.get("config", {}),
            "is_active": source_data.get("is_active", True),
            "created_at": datetime.now().isoformat()
        }
        
        # 실제로는 DB에 저장
        # self.db.add(...)
        # self.db.commit()
        
        return new_source
    
    def update_source(self, source_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        소스 정보 업데이트
        
        Args:
            source_id: 소스 ID
            update_data: 업데이트할 데이터
            
        Returns:
            업데이트된 소스 정보
        """
        source = self.get_source(source_id)
        if source:
            source.update(update_data)
            source["updated_at"] = datetime.now().isoformat()
            return source
        return None
    
    def delete_source(self, source_id: str) -> bool:
        """
        소스 삭제
        
        Args:
            source_id: 소스 ID
            
        Returns:
            성공 여부
        """
        source = self.get_source(source_id)
        if source:
            # 실제로는 DB에서 삭제
            # self.db.delete(...)
            # self.db.commit()
            return True
        return False
    
    def test_source(self, source_id: str) -> Dict[str, Any]:
        """
        소스 연결 테스트
        
        Args:
            source_id: 소스 ID
            
        Returns:
            테스트 결과
        """
        source = self.get_source(source_id)
        if not source:
            return {"success": False, "message": "Source not found"}
        
        # 실제로는 URL 연결 테스트 수행
        import requests
        try:
            response = requests.head(source["url"], timeout=5)
            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "message": "Connection successful" if response.status_code < 400 else f"HTTP {response.status_code}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }
