from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import json
import heapq
from app.models import OsintTask, TaskResult, TaskQueue, TaskDependency, WorkerNode, TaskStatus, TaskPriority, TaskType

class PriorityCalculator:
    @staticmethod
    def calculate_priority_score(task: OsintTask) -> float:
        base_scores = {
            TaskPriority.CRITICAL: 1000,
            TaskPriority.HIGH: 100,
            TaskPriority.MEDIUM: 10,
            TaskPriority.LOW: 1
        }
        
        score = base_scores.get(task.priority, 10)
        
        # Time-based urgency (older tasks get higher priority)
        age_hours = (datetime.utcnow() - task.created_at).total_seconds() / 3600
        score += age_hours * 0.1
        
        # Keyword urgency (pension-related keywords get higher priority)
        urgent_keywords = ["pension", "retire", "annuity", "투자", "연금"]
        keyword_boost = sum(1 for keyword in task.keywords 
                          if any(urgent in keyword.lower() for urgent in urgent_keywords))
        score += keyword_boost * 5
        
        # Dependency boost (tasks with dependents get higher priority)
        score += len(task.dependencies) * 2
        
        return score

class TaskOrchestrator:
    def __init__(self):
        self.tasks = {}
        self.task_queue = []
        self.workers = {}
        self.results = {}
        self.dependencies = {}
        
    async def create_task(self, task_type: str, keywords: List[str], sources: List[str],
                         priority: str = "medium", metadata: Optional[Dict[str, Any]] = None,
                         dependencies: Optional[List[str]] = None, timeout_seconds: int = 3600,
                         expected_results: int = 0) -> str:
        task_id = str(uuid.uuid4())
        
        task = OsintTask(
            id=task_id,
            task_type=TaskType(task_type),
            keywords=keywords,
            sources=sources,
            priority=TaskPriority(priority),
            metadata=(metadata or {}),
            dependencies=dependencies or [],
            timeout_seconds=timeout_seconds,
            expected_results=expected_results
        )
        
        self.tasks[task_id] = task
        
        # Add to priority queue if no dependencies or all dependencies are met
        if await self._dependencies_met(task_id):
            priority_score = PriorityCalculator.calculate_priority_score(task)
            heapq.heappush(self.task_queue, (-priority_score, task_id))
        
        # Publish task created event
        await self._publish_event("task.created", {
            "task_id": task_id,
            "task_type": task_type,
            "keywords": keywords,
            "sources": sources,
            "priority": priority
        })
        
        return task_id
    
    async def update_task(self, task_id: str, status: Optional[str] = None,
                         assigned_to: Optional[str] = None, priority: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None,
                         error_message: Optional[str] = None) -> bool:
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        old_status = task.status
        
        if status:
            task.status = TaskStatus(status)
            if status == TaskStatus.IN_PROGRESS:
                task.started_at = datetime.utcnow()
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                task.completed_at = datetime.utcnow()
        
        if assigned_to:
            task.assigned_to = assigned_to
        
        if priority:
            task.priority = TaskPriority(priority)
            # Re-prioritize in queue if task is still pending
            if task.status == TaskStatus.PENDING:
                await self._reprioritize_task(task_id)
        
        if metadata:
            task.metadata.update(metadata)
        
        if error_message:
            task.error_message = error_message
        
        task.updated_at = datetime.utcnow()
        
        # Handle status changes
        if old_status != task.status:
            await self._handle_status_change(task_id, old_status, task.status)
        
        # Publish task updated event
        await self._publish_event("task.updated", {
            "task_id": task_id,
            "old_status": old_status,
            "new_status": task.status,
            "assigned_to": assigned_to
        })
        
        return True
    
    async def get_next_tasks(self, worker_capabilities: List[str], max_tasks: int = 1) -> List[OsintTask]:
        assigned_tasks = []
        
        # Create a copy of the queue to iterate through
        temp_queue = list(self.task_queue)
        new_queue = []
        
        for priority_score, task_id in temp_queue:
            if len(assigned_tasks) >= max_tasks:
                new_queue.append((priority_score, task_id))
                continue
            
            if task_id not in self.tasks:
                continue  # Skip deleted tasks
            
            task = self.tasks[task_id]
            
            # Check if worker can handle this task type
            if task.task_type.value not in worker_capabilities:
                new_queue.append((priority_score, task_id))
                continue
            
            # Check if dependencies are met
            if not await self._dependencies_met(task_id):
                new_queue.append((priority_score, task_id))
                continue
            
            # Assign task
            task.status = TaskStatus.ASSIGNED
            task.updated_at = datetime.utcnow()
            assigned_tasks.append(task)
        
        # Update the queue
        self.task_queue = new_queue
        heapq.heapify(self.task_queue)
        
        return assigned_tasks
    
    async def submit_result(self, task_id: str, result_type: str, data: Dict[str, Any],
                           quality_score: float = 0.0, confidence_score: float = 0.0) -> str:
        result_id = str(uuid.uuid4())
        
        result = TaskResult(
            id=result_id,
            task_id=task_id,
            result_type=result_type,
            data=data,
            quality_score=quality_score,
            confidence_score=confidence_score
        )
        
        if task_id not in self.results:
            self.results[task_id] = []
        self.results[task_id].append(result)
        
        # Publish result event
        await self._publish_event("task.result", {
            "result_id": result_id,
            "task_id": task_id,
            "result_type": result_type,
            "quality_score": quality_score,
            "confidence_score": confidence_score
        })
        
        return result_id
    
    async def register_worker(self, node_id: str, node_type: str, capabilities: List[str],
                             max_concurrent_tasks: int = 5, metadata: Optional[Dict[str, Any]] = None) -> str:
        worker_id = str(uuid.uuid4())
        
        worker = WorkerNode(
            id=worker_id,
            node_id=node_id,
            node_type=node_type,
            capabilities=capabilities,
            max_concurrent_tasks=max_concurrent_tasks,
            metadata=(metadata or {}),
            last_heartbeat=datetime.utcnow()
        )
        
        self.workers[worker_id] = worker
        
        # Publish worker registered event
        await self._publish_event("worker.registered", {
            "worker_id": worker_id,
            "node_id": node_id,
            "capabilities": capabilities
        })
        
        return worker_id
    
    async def worker_heartbeat(self, worker_id: str, current_load: int = 0) -> bool:
        if worker_id not in self.workers:
            return False
        
        worker = self.workers[worker_id]
        worker.last_heartbeat = datetime.utcnow()
        worker.current_load = current_load
        worker.updated_at = datetime.utcnow()
        
        return True
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        total_tasks = len(self.tasks)
        status_counts = {}
        
        for task in self.tasks.values():
            status_counts[task.status] = status_counts.get(task.status, 0) + 1
        
        # Calculate average completion time
        completed_tasks = [t for t in self.tasks.values() 
                          if t.status == TaskStatus.COMPLETED and t.completed_at and t.started_at]
        avg_completion_time = 0.0
        if completed_tasks:
            total_time = sum((t.completed_at - t.started_at).total_seconds() for t in completed_tasks)
            avg_completion_time = total_time / len(completed_tasks)
        
        # Calculate throughput (tasks completed per hour in last 24h)
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_completed = [t for t in completed_tasks if t.completed_at >= last_24h]
        throughput = len(recent_completed) / 24.0  # tasks per hour
        
        return {
            "total_tasks": total_tasks,
            "pending_tasks": status_counts.get(TaskStatus.PENDING, 0),
            "in_progress_tasks": status_counts.get(TaskStatus.IN_PROGRESS, 0),
            "completed_tasks": status_counts.get(TaskStatus.COMPLETED, 0),
            "failed_tasks": status_counts.get(TaskStatus.FAILED, 0),
            "average_completion_time": avg_completion_time,
            "queue_throughput": throughput,
            "active_workers": len([w for w in self.workers.values() if w.status == "active"])
        }

    async def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[str] = None,
    ) -> List[OsintTask]:
        tasks = list(self.tasks.values())

        if status:
            try:
                status_enum = TaskStatus(status)
                tasks = [t for t in tasks if t.status == status_enum]
            except ValueError:
                tasks = []

        if priority and tasks:
            try:
                priority_enum = TaskPriority(priority)
                tasks = [t for t in tasks if t.priority == priority_enum]
            except ValueError:
                tasks = []

        if assigned_to and tasks:
            tasks = [t for t in tasks if t.assigned_to == assigned_to]

        tasks.sort(key=lambda t: t.created_at)  # oldest first
        return tasks
    
    async def _dependencies_met(self, task_id: str) -> bool:
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        for dep_task_id in task.dependencies:
            if dep_task_id not in self.tasks:
                return False
            if self.tasks[dep_task_id].status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    async def _reprioritize_task(self, task_id: str):
        # Remove task from queue if it exists
        self.task_queue = [(score, tid) for score, tid in self.task_queue if tid != task_id]
        heapq.heapify(self.task_queue)
        
        # Re-add with new priority
        if task_id in self.tasks and self.tasks[task_id].status == TaskStatus.PENDING:
            priority_score = PriorityCalculator.calculate_priority_score(self.tasks[task_id])
            heapq.heappush(self.task_queue, (-priority_score, task_id))
    
    async def _handle_status_change(self, task_id: str, old_status: TaskStatus, new_status: TaskStatus):
        # Handle task completion - check for dependent tasks
        if new_status == TaskStatus.COMPLETED:
            await self._check_dependent_tasks(task_id)
        
        # Handle task failure - retry logic
        elif new_status == TaskStatus.FAILED:
            await self._handle_task_failure(task_id)
    
    async def _check_dependent_tasks(self, completed_task_id: str):
        # Find tasks that depend on this completed task
        for task_id, task in self.tasks.items():
            if (completed_task_id in task.dependencies and 
                task.status == TaskStatus.PENDING and
                await self._dependencies_met(task_id)):
                
                # Add to queue
                priority_score = PriorityCalculator.calculate_priority_score(task)
                heapq.heappush(self.task_queue, (-priority_score, task_id))
    
    async def _handle_task_failure(self, task_id: str):
        task = self.tasks[task_id]
        
        if task.retry_count < task.max_retries:
            # Retry the task
            task.retry_count += 1
            task.status = TaskStatus.PENDING
            task.assigned_to = None
            task.error_message = None
            task.updated_at = datetime.utcnow()
            
            # Re-add to queue
            priority_score = PriorityCalculator.calculate_priority_score(task)
            heapq.heappush(self.task_queue, (-priority_score, task_id))
            
            await self._publish_event("task.retry", {
                "task_id": task_id,
                "retry_count": task.retry_count,
                "max_retries": task.max_retries
            })
    
    async def _publish_event(self, event_type: str, data: Dict[str, Any]):
        # Event publishing stub - integrate with Kafka/NATS in production
        event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        print(f"Event published: {json.dumps(event)}")

# Global orchestrator instance
orchestrator = TaskOrchestrator()