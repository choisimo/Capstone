from typing import List, Optional, Dict, Any
from app.services.keyword_service import planning_service
from app.schemas import (
    PlanCreateRequest, PlanUpdateRequest, PlanResponse, 
    PlanExecutionRequest, PlanExecutionResponse, PlanRecommendationRequest, PlanRecommendationResponse
)

# Mock FastAPI router
class APIRouter:
    def __init__(self, prefix="", tags=None):
        self.prefix = prefix
        self.tags = tags or []
        self.routes = []
    
    def post(self, path):
        def decorator(func):
            self.routes.append(("POST", self.prefix + path, func))
            return func
        return decorator
    
    def get(self, path):
        def decorator(func):
            self.routes.append(("GET", self.prefix + path, func))
            return func
        return decorator
    
    def put(self, path):
        def decorator(func):
            self.routes.append(("PUT", self.prefix + path, func))
            return func
        return decorator

router = APIRouter(prefix="/api/v1/plans", tags=["plans"])

@router.post("/")
async def create_plan(request: PlanCreateRequest) -> Dict[str, str]:
    """Create a new OSINT collection plan"""
    plan_id = await planning_service.create_plan(
        title=request.title,
        description=request.description,
        query=request.query,
        objectives=request.objectives,
        strategy=request.strategy,
        keywords=request.keywords,
        sources=request.sources,
        schedule=request.schedule,
        metadata=request.metadata
    )
    
    return {"plan_id": plan_id, "status": "created"}

@router.get("/{plan_id}")
async def get_plan(plan_id: str) -> PlanResponse:
    """Get a specific plan by ID"""
    if plan_id not in planning_service.plans:
        raise ValueError("Plan not found")
    
    plan = planning_service.plans[plan_id]
    
    return PlanResponse(
        plan_id=plan.plan_id,
        title=plan.title,
        description=plan.description,
        query=plan.query,
        objectives=plan.objectives,
        strategy=plan.strategy.value,
        keywords=plan.keywords,
        sources=plan.sources,
        schedule=plan.schedule,
        status=plan.status.value,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        metadata=plan.metadata
    )

@router.put("/{plan_id}")
async def update_plan(plan_id: str, request: PlanUpdateRequest) -> Dict[str, str]:
    """Update an existing plan"""
    updates = {}
    if request.title is not None:
        updates["title"] = request.title
    if request.description is not None:
        updates["description"] = request.description
    if request.status is not None:
        updates["status"] = request.status
    if request.strategy is not None:
        updates["strategy"] = request.strategy
    if request.keywords is not None:
        updates["keywords"] = request.keywords
    if request.sources is not None:
        updates["sources"] = request.sources
    if request.metadata is not None:
        updates["metadata"] = request.metadata
    
    success = await planning_service.update_plan(plan_id, updates)
    
    if not success:
        raise ValueError("Plan not found")
    
    return {"plan_id": plan_id, "status": "updated"}

@router.post("/{plan_id}/execute")
async def execute_plan(plan_id: str, request: PlanExecutionRequest) -> Dict[str, str]:
    """Execute a plan by creating collection tasks"""
    execution_id = await planning_service.execute_plan(
        plan_id=plan_id,
        execution_params=request.execution_params
    )
    
    return {"execution_id": execution_id, "status": "started"}

@router.get("/{plan_id}/executions/{execution_id}")
async def get_execution_status(plan_id: str, execution_id: str) -> PlanExecutionResponse:
    """Get the status of a plan execution"""
    status = await planning_service.get_execution_status(execution_id)
    
    return PlanExecutionResponse(
        execution_id=status["execution_id"],
        plan_id=status["plan_id"],
        status=status["status"],
        started_at=status["started_at"],
        completed_at=status["completed_at"],
        tasks_created=status["tasks_created"],
        results_collected=status["results_collected"],
        progress=status["progress"],
        errors=status["errors"],
        metadata=status["metadata"]
    )

@router.post("/recommendations")
async def get_plan_recommendations(request: PlanRecommendationRequest) -> PlanRecommendationResponse:
    """Get AI-powered recommendations for creating a plan"""
    recommendations = await planning_service.get_plan_recommendations(
        query=request.query,
        context=request.context
    )
    
    return PlanRecommendationResponse(
        recommended_keywords=recommendations["recommended_keywords"],
        recommended_strategy=recommendations["recommended_strategy"],
        recommended_sources=recommendations["recommended_sources"],
        suggested_schedule=recommendations["suggested_schedule"],
        suggested_objectives=recommendations["suggested_objectives"],
        confidence_score=recommendations["confidence_score"]
    )

@router.get("/")
async def list_plans(status: Optional[str] = None, strategy: Optional[str] = None) -> List[PlanResponse]:
    """List all plans with optional filters"""
    plans = []
    
    for plan in planning_service.plans.values():
        # Apply filters
        if status and plan.status.value != status:
            continue
        if strategy and plan.strategy.value != strategy:
            continue
        
        plans.append(PlanResponse(
            plan_id=plan.plan_id,
            title=plan.title,
            description=plan.description,
            query=plan.query,
            objectives=plan.objectives,
            strategy=plan.strategy.value,
            keywords=plan.keywords,
            sources=plan.sources,
            schedule=plan.schedule,
            status=plan.status.value,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
            metadata=plan.metadata
        ))
    
    return plans

@router.get("/analytics/dashboard")
async def get_planning_dashboard() -> Dict[str, Any]:
    """Get planning analytics dashboard data"""
    plans = planning_service.plans
    executions = planning_service.executions
    
    # Calculate statistics
    total_plans = len(plans)
    active_plans = sum(1 for p in plans.values() if p.status.value == "active")
    total_executions = len(executions)
    running_executions = sum(1 for e in executions.values() if e.status == "running")
    
    # Strategy distribution
    strategy_counts = {}
    for plan in plans.values():
        strategy = plan.strategy.value
        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
    
    return {
        "total_plans": total_plans,
        "active_plans": active_plans,
        "total_executions": total_executions,
        "running_executions": running_executions,
        "strategy_distribution": strategy_counts,
        "average_keywords_per_plan": sum(len(p.keywords) for p in plans.values()) / max(total_plans, 1),
        "average_sources_per_plan": sum(len(p.sources) for p in plans.values()) / max(total_plans, 1)
    }