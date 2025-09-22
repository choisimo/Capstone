from typing import List, Optional, Dict
from datetime import datetime
import asyncio

class KeywordType:
    SEED = "seed"
    EXPANDED = "expanded"
    ALIAS = "alias"

class KeywordStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"  
    PENDING = "pending"

class OsintKeyword:
    def __init__(self, id=None, term="", lang="ko", type=KeywordType.SEED, 
                 importance=1.0, status=KeywordStatus.PENDING, metadata=None):
        self.id = id
        self.term = term
        self.lang = lang
        self.type = type
        self.importance = importance
        self.status = status
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.metadata = metadata or {}

class OsintKeywordRelation:
    def __init__(self, keyword_id, related_keyword_id, relation_type, weight=1.0):
        self.id = None
        self.keyword_id = keyword_id
        self.related_keyword_id = related_keyword_id
        self.relation_type = relation_type
        self.weight = weight
        self.created_at = datetime.utcnow()