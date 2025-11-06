from typing import Optional, List, Dict, Any
from datetime import datetime


class PlanCreateRequest:
    def __init__(self, title: str, description: str, query: str, objectives: List[str],
                 strategy: str = "targeted", keywords: Optional[List[str]] = None,
                 sources: Optional[List[Dict[str, Any]]] = None, 
                 schedule: Optional[Dict[str, Any]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.title = title
        self.description = description
        self.query = query
        self.objectives = objectives
        self.strategy = strategy
        self.keywords = keywords
        self.sources = sources
        self.schedule = schedule
        self.metadata = metadata


class PlanUpdateRequest:
    def __init__(self, title: Optional[str] = None, description: Optional[str] = None,
                 status: Optional[str] = None, strategy: Optional[str] = None,
                 keywords: Optional[List[str]] = None, sources: Optional[List[Dict[str, Any]]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.title = title
        self.description = description
        self.status = status
        self.strategy = strategy
        self.keywords = keywords
        self.sources = sources
        self.metadata = metadata


class PlanResponse:
    def __init__(self, plan_id: str, title: str, description: str, query: str,
                 objectives: List[str], strategy: str, keywords: List[str],
                 sources: List[Dict[str, Any]], schedule: Optional[Dict[str, Any]],
                 status: str, created_at: datetime, updated_at: datetime,
                 metadata: Dict[str, Any]):
        self.plan_id = plan_id
        self.title = title
        self.description = description
        self.query = query
        self.objectives = objectives
        self.strategy = strategy
        self.keywords = keywords
        self.sources = sources
        self.schedule = schedule
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.metadata = metadata


class PlanExecutionRequest:
    def __init__(self, execution_params: Optional[Dict[str, Any]] = None):
        self.execution_params = execution_params or {}


class PlanExecutionResponse:
    def __init__(self, execution_id: str, plan_id: str, status: str,
                 started_at: Optional[datetime], completed_at: Optional[datetime],
                 tasks_created: int, results_collected: int, progress: float,
                 errors: List[str], metadata: Dict[str, Any]):
        self.execution_id = execution_id
        self.plan_id = plan_id
        self.status = status
        self.started_at = started_at
        self.completed_at = completed_at
        self.tasks_created = tasks_created
        self.results_collected = results_collected
        self.progress = progress
        self.errors = errors
        self.metadata = metadata


class PlanRecommendationRequest:
    def __init__(self, query: str, context: Optional[Dict[str, Any]] = None):
        self.query = query
        self.context = context or {}


class PlanRecommendationResponse:
    def __init__(self, recommended_keywords: List[str], recommended_strategy: str,
                 recommended_sources: List[Dict[str, Any]], suggested_schedule: Dict[str, Any],
                 suggested_objectives: List[str], confidence_score: float):
        self.recommended_keywords = recommended_keywords
        self.recommended_strategy = recommended_strategy
        self.recommended_sources = recommended_sources
        self.suggested_schedule = suggested_schedule
        self.suggested_objectives = suggested_objectives
        self.confidence_score = confidence_score