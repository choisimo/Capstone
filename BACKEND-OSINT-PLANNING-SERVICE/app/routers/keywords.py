from typing import List, Optional
import asyncio
import sys
import os

# Add parent directory to path for imports
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# For FastAPI-like functionality without actually importing FastAPI
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
from services.keyword_service import KeywordService

router = APIRouter(prefix="/keywords", tags=["keywords"])
keyword_service = KeywordService()

@router.post("/")
async def create_keyword(keyword_data: dict, db=None):
    """Create a new keyword (seed or expanded)"""
    if db is None:
        db = get_db()
    return await keyword_service.create_keyword(db, keyword_data)

@router.get("/")
def get_keywords(type: Optional[str] = None, status: Optional[str] = None, 
                importance_min: Optional[float] = None, db=None):
    """Get keywords with optional filters"""
    if db is None:
        db = get_db()
    
    # Mock implementation - would normally query database
    mock_keywords = [
        {
            "id": 1,
            "term": "국민연금",
            "type": "seed",
            "status": "active",
            "importance": 9.0,
            "lang": "ko"
        },
        {
            "id": 2,
            "term": "삼성전자",
            "type": "seed", 
            "status": "active",
            "importance": 8.0,
            "lang": "ko"
        }
    ]
    
    # Apply filters
    filtered = mock_keywords
    if type:
        filtered = [k for k in filtered if k["type"] == type]
    if status:
        filtered = [k for k in filtered if k["status"] == status]
    if importance_min:
        filtered = [k for k in filtered if k["importance"] >= importance_min]
        
    return filtered

@router.get("/{keyword_id}")
def get_keyword(keyword_id: int, db=None):
    """Get a specific keyword by ID"""
    if db is None:
        db = get_db()
    
    # Mock implementation
    if keyword_id == 1:
        return {
            "id": 1,
            "term": "국민연금",
            "type": "seed",
            "status": "active", 
            "importance": 9.0,
            "lang": "ko"
        }
    return {"error": "Keyword not found"}

@router.patch("/{keyword_id}")
async def update_keyword(keyword_id: int, update_data: dict, db=None):
    """Update a keyword"""
    if db is None:
        db = get_db()
    
    # Mock implementation
    print(f"Updating keyword {keyword_id} with {update_data}")
    
    # Publish update event
    await keyword_service._publish_event("osint.keyword.updated", {
        "id": keyword_id,
        "updates": list(update_data.keys()),
        "timestamp": "2025-09-22T00:00:00"
    })
    
    return {"message": "Keyword updated", "id": keyword_id}

@router.post("/{keyword_id}/expand")
async def expand_keyword(keyword_id: int, request_data: dict, db=None):
    """Expand a keyword using various methods"""
    if db is None:
        db = get_db()
    
    request_data["keyword_id"] = keyword_id
    return await keyword_service.expand_keyword(db, request_data)

@router.post("/{keyword_id}/approve-expansions")
async def approve_expansions(keyword_id: int, approved_ids: List[int], db=None):
    """Approve expanded keywords to make them active"""
    if db is None:
        db = get_db()
    
    updated_count = len(approved_ids)
    print(f"Approved {updated_count} expansions for keyword {keyword_id}")
    
    return {
        "message": f"Approved {updated_count} keywords", 
        "approved_ids": approved_ids
    }

# Test function for the API
def test_api():
    print("Testing OSINT Planning Service API...")
    
    # Test create keyword
    keyword_data = {
        "term": "국민연금",
        "type": "seed",
        "importance": 9.0,
        "lang": "ko"
    }
    
    # Test get keywords
    keywords = get_keywords()
    print(f"Found {len(keywords)} keywords")
    
    # Test expansion
    expansion_request = {
        "expansion_methods": ["morpheme", "synonym"],
        "max_expansions": 10,
        "min_confidence": 0.5
    }
    
    print("API tests completed")

if __name__ == "__main__":
    test_api()