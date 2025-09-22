from typing import List, Optional, Dict
import asyncio
import sys
import os

# Add parent directory to path for imports
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Mock HTTP client for environments without aiohttp
class MockHTTPResponse:
    def __init__(self, status=200, headers=None, text=""):
        self.status = status
        self.headers = headers or {}
        self._text = text
    
    async def text(self):
        return self._text
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass

class MockHTTPSession:
    async def get(self, url, timeout=10):
        # Mock robots.txt responses
        if "robots.txt" in url:
            return MockHTTPResponse(200, {}, "User-agent: *\nDisallow:")
        return MockHTTPResponse(200, {"content-type": "text/html"})
    
    async def head(self, url, timeout=15):
        return MockHTTPResponse(200, {
            "content-type": "text/html",
            "server": "nginx",
            "last-modified": "Mon, 01 Jan 2024 00:00:00 GMT"
        })
    
    async def close(self):
        pass

# For FastAPI-like functionality
class APIRouter:
    def __init__(self, prefix="", tags=None):
        self.prefix = prefix
        self.tags = tags or []
        self.routes = []
    
    def post(self, path):
        def decorator(func):
            self.routes.append(("POST", path, func))
            return func
        return decorator
    
    def get(self, path):
        def decorator(func):
            self.routes.append(("GET", path, func))
            return func
        return decorator
    
    def patch(self, path):
        def decorator(func):
            self.routes.append(("PATCH", path, func))
            return func
        return decorator

# Mock dependencies
def get_db():
    class MockDB:
        def __init__(self):
            self.data = {}
        def add(self, obj): pass
        def commit(self): pass
        def refresh(self, obj): pass
        def query(self, model): 
            class MockQuery:
                def filter(self, *args): return self
                def first(self): return None
                def all(self): return []
            return MockQuery()
    return MockDB()

# Import the service
from services.source_service import SourceService
from models import SourceCategory, SourceStatus

router = APIRouter(prefix="/sources", tags=["sources"])
source_service = SourceService()

@router.post("/")
async def register_source(source_data: dict, db=None):
    """Register a new source"""
    if db is None:
        db = get_db()
    
    url = source_data.get("url", "")
    if not url:
        return {"error": "URL is required"}
        
    category = source_data.get("category", SourceCategory.OTHER)
    region = source_data.get("region", "KR")
    
    return await source_service.register_source(db, url, category, region)

@router.get("/")
def get_sources(status: Optional[str] = None, category: Optional[str] = None,
               trust_min: Optional[float] = None, db=None):
    """Get sources with optional filters"""
    if db is None:
        db = get_db()
    
    # Mock sources
    mock_sources = [
        {
            "id": 1,
            "url": "https://news.naver.com",
            "host": "news.naver.com",
            "category": SourceCategory.NEWS,
            "status": SourceStatus.ACTIVE,
            "trust_score": 0.9,
            "region": "KR"
        },
        {
            "id": 2,
            "url": "https://www.chosun.com",
            "host": "www.chosun.com", 
            "category": SourceCategory.NEWS,
            "status": SourceStatus.ACTIVE,
            "trust_score": 0.85,
            "region": "KR"
        }
    ]
    
    # Apply filters
    filtered = mock_sources
    if status:
        filtered = [s for s in filtered if s["status"] == status]
    if category:
        filtered = [s for s in filtered if s["category"] == category]
    if trust_min:
        filtered = [s for s in filtered if s["trust_score"] >= trust_min]
        
    return filtered

@router.get("/{source_id}")
def get_source(source_id: int, db=None):
    """Get a specific source by ID"""
    if db is None:
        db = get_db()
    
    # Mock implementation
    if source_id == 1:
        return {
            "id": 1,
            "url": "https://news.naver.com",
            "host": "news.naver.com",
            "category": SourceCategory.NEWS,
            "status": SourceStatus.ACTIVE,
            "trust_score": 0.9,
            "region": "KR"
        }
    return {"error": "Source not found"}

@router.patch("/{source_id}")
async def update_source(source_id: int, update_data: dict, db=None):
    """Update a source"""
    if db is None:
        db = get_db()
    
    print(f"Updating source {source_id} with {update_data}")
    
    # Publish update event
    await source_service._publish_event("osint.source.updated", {
        "id": source_id,
        "updates": list(update_data.keys()),
        "timestamp": "2025-09-22T00:00:00"
    })
    
    return {"message": "Source updated", "id": source_id}

@router.post("/bulk-register")
async def bulk_register_sources(sources_data: dict, db=None):
    """Register multiple sources in bulk"""
    if db is None:
        db = get_db()
    
    sources_list = sources_data.get("sources", [])
    return await source_service.bulk_register_sources(db, sources_list)

@router.get("/crawlable")
async def get_crawlable_sources(limit: int = 100, db=None):
    """Get sources ready for crawling"""
    if db is None:
        db = get_db()
    
    return await source_service.get_crawlable_sources(db, limit)

@router.post("/{source_id}/metrics")
async def update_source_metrics(source_id: int, metrics_data: dict, db=None):
    """Update source metrics after crawling"""
    if db is None:
        db = get_db()
    
    await source_service.update_source_metrics(db, source_id, metrics_data)
    return {"message": "Metrics updated", "source_id": source_id}

@router.post("/validate")
async def validate_source_url(url_data: dict):
    """Validate a source URL"""
    url = url_data.get("url", "")
    if not url:
        return {"error": "URL is required"}
    return await source_service.validate_source_url(url)

# Test function for the API
async def test_api():
    print("Testing OSINT Source Service API...")
    
    # Test register source
    source_data = {
        "url": "https://news.naver.com",
        "category": SourceCategory.NEWS,
        "region": "KR"
    }
    
    try:
        source = await register_source(source_data)
        print(f"Registered source: {source_data['url']}")
    except Exception as e:
        print(f"Registration error: {e}")
    
    # Test get sources
    sources = get_sources()
    print(f"Found {len(sources)} sources")
    
    # Test bulk register
    bulk_data = {
        "sources": [
            {"url": "https://www.chosun.com", "category": SourceCategory.NEWS},
            {"url": "https://www.hani.co.kr", "category": SourceCategory.NEWS}
        ]
    }
    
    try:
        bulk_result = await bulk_register_sources(bulk_data)
        print(f"Bulk registration: {bulk_result}")
    except Exception as e:
        print(f"Bulk registration error: {e}")
    
    # Test crawlable sources
    try:
        crawlable = await get_crawlable_sources(10)
        print(f"Crawlable sources: {len(crawlable)}")
    except Exception as e:
        print(f"Crawlable sources error: {e}")
    
    print("API tests completed")

if __name__ == "__main__":
    asyncio.run(test_api())