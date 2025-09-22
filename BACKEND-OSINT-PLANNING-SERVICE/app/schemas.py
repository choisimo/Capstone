from typing import Optional, List, Dict
from datetime import datetime

class KeywordTypeEnum:
    seed = "seed"
    expanded = "expanded"
    alias = "alias"

class KeywordStatusEnum:
    active = "active"
    inactive = "inactive"
    pending = "pending"

class KeywordBase:
    def __init__(self, term: str, lang: str = "ko", importance: float = 1.0, metadata: Optional[Dict] = None):
        self.term = term
        self.lang = lang
        self.importance = max(0, min(10, importance))  # Clamp between 0-10
        self.metadata = metadata or {}

class KeywordCreate(KeywordBase):
    def __init__(self, term: str, lang: str = "ko", importance: float = 1.0, 
                 type: str = KeywordTypeEnum.seed, metadata: Optional[Dict] = None):
        super().__init__(term, lang, importance, metadata)
        self.type = type

class KeywordUpdate:
    def __init__(self, term: Optional[str] = None, importance: Optional[float] = None,
                 status: Optional[str] = None, metadata: Optional[Dict] = None):
        self.term = term
        self.importance = importance
        self.status = status
        self.metadata = metadata

class KeywordResponse(KeywordBase):
    def __init__(self, id: int, term: str, lang: str, type: str, status: str,
                 importance: float, created_at: datetime, updated_at: datetime, metadata: Optional[Dict] = None):
        super().__init__(term, lang, importance, metadata)
        self.id = id
        self.type = type
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

class KeywordExpansionRequest:
    def __init__(self, keyword_id: int, expansion_methods: Optional[List[str]] = None, 
                 max_expansions: int = 30, min_confidence: float = 0.3):
        self.keyword_id = keyword_id
        self.expansion_methods = expansion_methods or ["morpheme", "synonym", "cooccurrence"]
        self.max_expansions = max_expansions
        self.min_confidence = min_confidence

class KeywordRelation:
    def __init__(self, keyword_id: int, related_keyword_id: int, relation_type: str, weight: float = 1.0):
        self.keyword_id = keyword_id
        self.related_keyword_id = related_keyword_id
        self.relation_type = relation_type
        self.weight = weight

class ExpansionResult:
    def __init__(self, original_keyword: str, expanded_keywords: List[Dict[str, float]], 
                 method: str, timestamp: datetime):
        self.original_keyword = original_keyword
        self.expanded_keywords = expanded_keywords
        self.method = method
        self.timestamp = timestamp