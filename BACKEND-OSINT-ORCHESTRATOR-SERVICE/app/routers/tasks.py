from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from app.services.orchestrator_service import orchestrator
from app.schemas import (
    TaskCreateRequest, TaskUpdateRequest, TaskResponse, 
    TaskResultRequest, TaskResultResponse, QueueStatsResponse,
    WorkerRegistrationRequest, WorkerResponse, TaskAssignmentRequest, TaskAssignmentResponse
)

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

@router.post("/")
async def create_task(request: TaskCreateRequest) -> Dict[str, str]:
    task_id = await orchestrator.create_task(
        task_type=request.task_type,
        keywords=request.keywords,
        sources=request.sources,
        priority=request.priority,
        metadata=request.metadata,
        dependencies=request.dependencies,
        timeout_seconds=request.timeout_seconds,
        expected_results=request.expected_results
    )
    
    return {"task_id": task_id, "status": "created"}

@router.get("/{task_id}")
async def get_task(task_id: str) -> TaskResponse:
    if task_id not in orchestrator.tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = orchestrator.tasks[task_id]
    
    return TaskResponse(
        id=task.id,
        task_type=task.task_type.value,
        keywords=task.keywords,
        sources=task.sources,
        priority=task.priority.value,
        status=task.status.value,
        assigned_to=task.assigned_to,
        metadata=task.metadata,
        dependencies=task.dependencies,
        retry_count=task.retry_count,
        max_retries=task.max_retries,
        timeout_seconds=task.timeout_seconds,
        expected_results=task.expected_results,
        created_at=task.created_at,
        updated_at=task.updated_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        error_message=task.error_message
    )

@router.put("/{task_id}")
async def update_task(task_id: str, request: TaskUpdateRequest) -> Dict[str, str]:
    success = await orchestrator.update_task(
        task_id=task_id,
        status=request.status,
        assigned_to=request.assigned_to,
        priority=request.priority,
        metadata=request.metadata,
        error_message=request.error_message
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"task_id": task_id, "status": "updated"}

@router.post("/{task_id}/results")
async def submit_result(task_id: str, request: TaskResultRequest) -> Dict[str, str]:
    result_id = await orchestrator.submit_result(
        task_id=task_id,
        result_type=request.result_type,
        data=request.data,
        quality_score=request.quality_score,
        confidence_score=request.confidence_score
    )
    
    return {"result_id": result_id, "status": "submitted"}

@router.get("/{task_id}/results")
async def get_task_results(task_id: str) -> List[TaskResultResponse]:
    if task_id not in orchestrator.results:
        return []
    
    results = orchestrator.results[task_id]
    
    return [
        TaskResultResponse(
            id=result.id,
            task_id=result.task_id,
            result_type=result.result_type,
            data=result.data,
            quality_score=result.quality_score,
            confidence_score=result.confidence_score,
            created_at=result.created_at
        ) for result in results
    ]

@router.post("/assign")
async def assign_tasks(request: TaskAssignmentRequest) -> TaskAssignmentResponse:
    tasks = await orchestrator.get_next_tasks(
        worker_capabilities=request.worker_capabilities,
        max_tasks=request.max_tasks
    )
    
    task_responses = [
        TaskResponse(
            id=task.id,
            task_type=task.task_type.value,
            keywords=task.keywords,
            sources=task.sources,
            priority=task.priority.value,
            status=task.status.value,
            assigned_to=task.assigned_to,
            metadata=task.metadata,
            dependencies=task.dependencies,
            retry_count=task.retry_count,
            max_retries=task.max_retries,
            timeout_seconds=task.timeout_seconds,
            expected_results=task.expected_results,
            created_at=task.created_at,
            updated_at=task.updated_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            error_message=task.error_message
        ) for task in tasks
    ]
    
    return TaskAssignmentResponse(tasks=task_responses)

@router.get("/queue/stats")
async def get_queue_stats() -> QueueStatsResponse:
    stats = await orchestrator.get_queue_stats()
    
    return QueueStatsResponse(
        total_tasks=stats["total_tasks"],
        pending_tasks=stats["pending_tasks"],
        in_progress_tasks=stats["in_progress_tasks"],
        completed_tasks=stats["completed_tasks"],
        failed_tasks=stats["failed_tasks"],
        average_completion_time=stats["average_completion_time"],
        queue_throughput=stats["queue_throughput"]
    )

@router.post("/workers")
async def register_worker(request: WorkerRegistrationRequest) -> Dict[str, str]:
    worker_id = await orchestrator.register_worker(
        node_id=request.node_id,
        node_type=request.node_type,
        capabilities=request.capabilities,
        max_concurrent_tasks=request.max_concurrent_tasks,
        metadata=request.metadata
    )
    
    return {"worker_id": worker_id, "status": "registered"}

@router.post("/workers/{worker_id}/heartbeat")
async def worker_heartbeat(worker_id: str, current_load: int = 0) -> Dict[str, str]:
    success = await orchestrator.worker_heartbeat(worker_id, current_load)
    
    if not success:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    return {"worker_id": worker_id, "status": "heartbeat_received"}

@router.get("/workers")
async def list_workers() -> List[WorkerResponse]:
    workers = []
    
    for worker in orchestrator.workers.values():
        workers.append(WorkerResponse(
            id=worker.id,
            node_id=worker.node_id,
            node_type=worker.node_type,
            capabilities=worker.capabilities,
            max_concurrent_tasks=worker.max_concurrent_tasks,
            current_load=worker.current_load,
            status=worker.status,
            last_heartbeat=worker.last_heartbeat,
            metadata=worker.metadata,
            created_at=worker.created_at,
            updated_at=worker.updated_at
        ))
    
    return workers