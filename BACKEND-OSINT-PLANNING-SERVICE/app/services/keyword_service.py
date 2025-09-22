from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import json
from app.models import (
    OsintPlan, SourcePlan, KeywordPlan, CollectionSchedule, 
    PlanExecution, PlanStatus, CollectionStrategy, SourceType, KeywordType
)


class PlanningService:
    def __init__(self):
        self.plans = {}
        self.executions = {}
        self.schedules = {}
        
    async def create_plan(self, title: str, description: str, query: str,
                         objectives: List[str], strategy: str = "targeted",
                         keywords: Optional[List[str]] = None, sources: Optional[List[Dict[str, Any]]] = None,
                         schedule: Optional[Dict[str, Any]] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new OSINT collection plan"""
        plan_id = str(uuid.uuid4())
        
        plan = OsintPlan(
            plan_id=plan_id,
            title=title,
            description=description,
            query=query,
            objectives=objectives,
            strategy=CollectionStrategy(strategy),
            keywords=keywords or [],
            sources=sources or [],
            schedule=schedule,
            status=PlanStatus.DRAFT,
            metadata=metadata or {}
        )
        
        self.plans[plan_id] = plan
        
        # Auto-generate keywords if not provided
        if not keywords:
            expanded_keywords = await self._expand_keywords(query, objectives)
            plan.keywords.extend(expanded_keywords)
        
        # Auto-select sources if not provided
        if not sources:
            recommended_sources = await self._recommend_sources(query, strategy)
            plan.sources.extend(recommended_sources)
        
        # Create schedule if provided
        if schedule:
            schedule_id = await self._create_schedule(plan_id, schedule)
            plan.metadata["schedule_id"] = schedule_id
        
        await self._publish_event("plan.created", {
            "plan_id": plan_id,
            "title": title,
            "strategy": strategy,
            "keywords_count": len(plan.keywords),
            "sources_count": len(plan.sources)
        })
        
        return plan_id
    
    async def update_plan(self, plan_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing plan"""
        if plan_id not in self.plans:
            return False
        
        plan = self.plans[plan_id]
        old_status = plan.status
        
        for key, value in updates.items():
            if hasattr(plan, key):
                if key == "status":
                    plan.status = PlanStatus(value)
                elif key == "strategy":
                    plan.strategy = CollectionStrategy(value)
                else:
                    setattr(plan, key, value)
        
        plan.updated_at = datetime.utcnow()
        
        # Handle status changes
        if old_status != plan.status:
            await self._handle_status_change(plan_id, old_status, plan.status)
        
        await self._publish_event("plan.updated", {
            "plan_id": plan_id,
            "old_status": old_status,
            "new_status": plan.status,
            "changes": list(updates.keys())
        })
        
        return True
    
    async def execute_plan(self, plan_id: str, execution_params: Optional[Dict[str, Any]] = None) -> str:
        """Execute a plan by creating tasks"""
        if plan_id not in self.plans:
            raise ValueError("Plan not found")
        
        plan = self.plans[plan_id]
        if plan.status != PlanStatus.ACTIVE:
            raise ValueError("Plan must be active to execute")
        
        execution_id = str(uuid.uuid4())
        execution_params = execution_params or {}
        
        execution = PlanExecution(
            execution_id=execution_id,
            plan_id=plan_id,
            status="running",
            started_at=datetime.utcnow(),
            metadata=execution_params
        )
        
        self.executions[execution_id] = execution
        
        # Create tasks for each source
        tasks_created = 0
        for source in plan.sources:
            task_config = {
                "plan_id": plan_id,
                "execution_id": execution_id,
                "source": source,
                "keywords": plan.keywords,
                "query": plan.query,
                "objectives": plan.objectives
            }
            
            # Send task to orchestrator service
            await self._send_to_orchestrator(task_config)
            tasks_created += 1
        
        execution.tasks_created = tasks_created
        
        await self._publish_event("plan.execution.started", {
            "execution_id": execution_id,
            "plan_id": plan_id,
            "tasks_created": tasks_created
        })
        
        return execution_id
    
    async def get_plan_recommendations(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get AI-powered recommendations for a plan"""
        context = context or {}
        
        # Analyze query for key topics
        keywords = await self._extract_keywords(query)
        
        # Recommend strategy based on query characteristics
        strategy = await self._recommend_strategy(query, keywords)
        
        # Recommend sources based on content type
        sources = await self._recommend_sources(query, strategy)
        
        # Suggest collection schedule
        schedule = await self._suggest_schedule(query, strategy)
        
        # Generate objectives
        objectives = await self._generate_objectives(query, keywords)
        
        return {
            "recommended_keywords": keywords,
            "recommended_strategy": strategy,
            "recommended_sources": sources,
            "suggested_schedule": schedule,
            "suggested_objectives": objectives,
            "confidence_score": 0.85  # Mock confidence
        }
    
    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get the status of a plan execution"""
        if execution_id not in self.executions:
            raise ValueError("Execution not found")
        
        execution = self.executions[execution_id]
        
        # Mock progress calculation
        progress = 75.0 if execution.status == "running" else 100.0
        
        return {
            "execution_id": execution_id,
            "plan_id": execution.plan_id,
            "status": execution.status,
            "started_at": execution.started_at,
            "completed_at": execution.completed_at,
            "tasks_created": execution.tasks_created,
            "results_collected": execution.results_collected,
            "progress": progress,
            "errors": execution.errors,
            "metadata": execution.metadata
        }
    
    async def _expand_keywords(self, query: str, objectives: List[str]) -> List[str]:
        """AI-powered keyword expansion"""
        # Mock keyword expansion based on Korean OSINT requirements
        base_keywords = query.split()
        
        expansion_rules = {
            "연금": ["국민연금", "사적연금", "퇴직연금", "노령연금"],
            "투자": ["펀드", "주식", "채권", "부동산", "포트폴리오"],
            "삼성": ["삼성전자", "삼성그룹", "이재용", "반도체"],
            "정책": ["정부정책", "금융정책", "규제", "법안"]
        }
        
        expanded = []
        for keyword in base_keywords:
            if keyword in expansion_rules:
                expanded.extend(expansion_rules[keyword])
        
        # Add objective-based keywords
        for objective in objectives:
            if "감정" in objective or "sentiment" in objective.lower():
                expanded.extend(["긍정", "부정", "우려", "기대"])
        
        return list(set(expanded))
    
    async def _recommend_sources(self, query: str, strategy: str) -> List[Dict[str, Any]]:
        """Recommend sources based on query and strategy"""
        sources = []
        
        # News sources for general coverage
        sources.append({
            "source_type": "news",
            "name": "네이버 뉴스",
            "url": "https://news.naver.com",
            "priority": 8,
            "rate_limit": 20
        })
        
        # Social media for sentiment
        if "감정" in query or strategy == "monitoring":
            sources.append({
                "source_type": "social",
                "name": "트위터",
                "url": "https://twitter.com",
                "priority": 7,
                "rate_limit": 15
            })
        
        # Financial blogs for investment content
        if "투자" in query or "연금" in query:
            sources.append({
                "source_type": "blog",
                "name": "투자 블로그",
                "url": "https://blog.naver.com",
                "priority": 6,
                "rate_limit": 10
            })
        
        return sources
    
    async def _recommend_strategy(self, query: str, keywords: List[str]) -> str:
        """Recommend collection strategy"""
        if len(keywords) > 10:
            return "comprehensive"
        elif any(word in query for word in ["모니터링", "추적", "변화"]):
            return "monitoring"
        elif any(word in query for word in ["과거", "이력", "히스토리"]):
            return "historical"
        else:
            return "targeted"
    
    async def _suggest_schedule(self, query: str, strategy: str) -> Dict[str, Any]:
        """Suggest collection schedule"""
        if strategy == "monitoring":
            return {
                "frequency": "hourly",
                "duration": "7_days",
                "start_time": datetime.utcnow().isoformat()
            }
        elif strategy == "comprehensive":
            return {
                "frequency": "daily",
                "duration": "30_days",
                "start_time": datetime.utcnow().isoformat()
            }
        else:
            return {
                "frequency": "once",
                "duration": "immediate",
                "start_time": datetime.utcnow().isoformat()
            }
    
    async def _generate_objectives(self, query: str, keywords: List[str]) -> List[str]:
        """Generate collection objectives"""
        objectives = []
        
        # Default objectives
        objectives.append("키워드 관련 최신 정보 수집")
        
        # Sentiment analysis for social content
        if any(word in query for word in ["감정", "반응", "여론"]):
            objectives.append("감정 분석을 위한 텍스트 데이터 수집")
        
        # Trend analysis for time-series data
        if any(word in query for word in ["트렌드", "변화", "추이"]):
            objectives.append("시계열 트렌드 분석용 데이터 수집")
        
        # Entity recognition for companies/people
        if any(word in keywords for word in ["삼성", "LG", "현대"]):
            objectives.append("기업 관련 정보 및 인물 정보 수집")
        
        return objectives
    
    async def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query using NLP"""
        # Simple keyword extraction (in real implementation, use KoNLPy or similar)
        words = query.split()
        
        # Filter out stopwords and short words
        stopwords = ["의", "를", "을", "이", "가", "에", "와", "과", "으로", "에서"]
        keywords = [word for word in words if len(word) > 1 and word not in stopwords]
        
        return keywords[:10]  # Limit to 10 keywords
    
    async def _create_schedule(self, plan_id: str, schedule_config: Dict[str, Any]) -> str:
        """Create a collection schedule"""
        schedule_id = str(uuid.uuid4())
        
        schedule = CollectionSchedule(
            schedule_id=schedule_id,
            plan_id=plan_id,
            frequency=schedule_config.get("frequency", "daily"),
            start_time=datetime.fromisoformat(schedule_config.get("start_time", datetime.utcnow().isoformat())),
            end_time=datetime.fromisoformat(schedule_config["end_time"]) if schedule_config.get("end_time") else None,
            timezone=schedule_config.get("timezone", "UTC"),
            metadata=schedule_config
        )
        
        self.schedules[schedule_id] = schedule
        return schedule_id
    
    async def _send_to_orchestrator(self, task_config: Dict[str, Any]):
        """Send task to orchestrator service"""
        # Mock sending to orchestrator
        print(f"Sending task to orchestrator: {json.dumps(task_config, indent=2)}")
    
    async def _handle_status_change(self, plan_id: str, old_status: PlanStatus, new_status: PlanStatus):
        """Handle plan status changes"""
        if new_status == PlanStatus.ACTIVE:
            # Plan activated - could trigger automatic execution
            pass
        elif new_status == PlanStatus.COMPLETED:
            # Plan completed - cleanup resources
            pass
    
    async def _publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish event to message bus"""
        event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        print(f"Event published: {json.dumps(event)}")


# Global planning service instance
planning_service = PlanningService()