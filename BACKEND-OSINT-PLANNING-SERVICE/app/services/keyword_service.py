from typing import List, Optional, Dict
from datetime import datetime
import asyncio

# Import models and schemas
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

class KeywordService:
    def __init__(self):
        # Mock Korean morphological analyzer
        self.morphemes = {}
    
    async def create_keyword(self, db, keyword_data: Dict) -> OsintKeyword:
        db_keyword = OsintKeyword(
            term=keyword_data.get("term", ""),
            lang=keyword_data.get("lang", "ko"),
            type=keyword_data.get("type", KeywordType.SEED),
            importance=keyword_data.get("importance", 1.0),
            status=KeywordStatus.PENDING,
            metadata=keyword_data.get("metadata", {})
        )
        db_keyword.id = len(getattr(db, 'data', {})) + 1  # Mock ID generation
        db.add(db_keyword)
        db.commit()
        
        # Publish event
        await self._publish_event("osint.keyword.created", {
            "id": db_keyword.id,
            "term": db_keyword.term,
            "type": keyword_data.get("type", KeywordType.SEED),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return db_keyword
    
    async def expand_keyword(self, db, request_data: Dict) -> Dict:
        keyword_id = request_data.get("keyword_id")
        expansion_methods = request_data.get("expansion_methods", ["morpheme", "synonym", "cooccurrence"])
        max_expansions = request_data.get("max_expansions", 30)
        min_confidence = request_data.get("min_confidence", 0.3)
        
        # Mock keyword lookup
        keyword = OsintKeyword(id=keyword_id, term="국민연금", importance=9.0)
        
        expanded_terms = {}
        
        if "morpheme" in expansion_methods:
            morpheme_expansions = await self._expand_morpheme(keyword.term)
            expanded_terms.update(morpheme_expansions)
        
        if "synonym" in expansion_methods:
            synonym_expansions = await self._expand_synonym(keyword.term)
            expanded_terms.update(synonym_expansions)
        
        if "cooccurrence" in expansion_methods:
            cooccur_expansions = await self._expand_cooccurrence(keyword.term)
            expanded_terms.update(cooccur_expansions)
        
        # Filter by confidence and limit
        filtered_terms = {
            term: score for term, score in expanded_terms.items()
            if score >= min_confidence
        }
        sorted_terms = sorted(filtered_terms.items(), key=lambda x: x[1], reverse=True)
        final_terms = dict(sorted_terms[:max_expansions])
        
        # Create expanded keywords (mock)
        for term, confidence in final_terms.items():
            expanded_keyword = OsintKeyword(
                term=term,
                lang=keyword.lang,
                type=KeywordType.EXPANDED,
                importance=keyword.importance * confidence,
                status=KeywordStatus.PENDING,
                metadata={"parent_id": keyword.id, "confidence": confidence}
            )
            db.add(expanded_keyword)
            
            # Create relation
            relation = OsintKeywordRelation(
                keyword_id=keyword.id,
                related_keyword_id=expanded_keyword.id,
                relation_type="expansion",
                weight=confidence
            )
            db.add(relation)
        
        db.commit()
        
        # Publish event
        await self._publish_event("osint.keyword.expanded", {
            "original_id": keyword.id,
            "original_term": keyword.term,
            "expansions": list(final_terms.keys()),
            "count": len(final_terms),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "original_keyword": keyword.term,
            "expanded_keywords": [{"term": k, "confidence": v} for k, v in final_terms.items()],
            "method": ",".join(expansion_methods),
            "timestamp": datetime.utcnow()
        }
    
    async def _expand_morpheme(self, term: str) -> Dict[str, float]:
        """Korean morpheme-based expansion"""
        expansions = {}
        
        # Simple Korean morpheme analysis (mock)
        morpheme_rules = {
            "국민연금": ["국민", "연금", "노령연금"],
            "삼성전자": ["삼성", "전자", "반도체"],
            "AI": ["인공지능", "머신러닝"]
        }
        
        if term in morpheme_rules:
            for token in morpheme_rules[term]:
                if token != term and len(token) > 1:
                    expansions[token] = 0.8
        
        return expansions
    
    async def _expand_synonym(self, term: str) -> Dict[str, float]:
        """Synonym-based expansion using predefined dictionary"""
        synonym_dict = {
            "국민연금": ["노령연금", "공적연금", "연금"],
            "삼성": ["삼성전자", "삼성그룹", "Samsung"],
            "AI": ["인공지능", "머신러닝", "딥러닝"],
        }
        
        expansions = {}
        if term in synonym_dict:
            for syn in synonym_dict[term]:
                expansions[syn] = 0.7
        
        return expansions
    
    async def _expand_cooccurrence(self, term: str) -> Dict[str, float]:
        """Statistical co-occurrence based expansion"""
        cooccur_dict = {
            "국민연금": ["수령", "개혁", "고갈", "보험료"],
            "삼성": ["반도체", "스마트폰", "이재용", "실적"],
        }
        
        expansions = {}
        if term in cooccur_dict:
            for word in cooccur_dict[term]:
                expansions[word] = 0.5
        
        return expansions
    
    async def _publish_event(self, topic: str, data: Dict):
        """Publish event to message bus"""
        print(f"Publishing to {topic}: {data}")
        # In real implementation, this would connect to Kafka/NATS/RabbitMQ