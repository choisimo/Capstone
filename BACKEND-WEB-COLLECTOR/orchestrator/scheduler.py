"""
작업 스케줄러
정기적인 작업 실행 및 시간 기반 트리거 관리
"""
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import croniter
import uuid

logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """스케줄 타입"""
    ONCE = "once"  # 한 번만
    INTERVAL = "interval"  # 주기적
    CRON = "cron"  # Cron 표현식
    DAILY = "daily"  # 매일
    WEEKLY = "weekly"  # 매주
    MONTHLY = "monthly"  # 매월


class JobStatus(Enum):
    """작업 상태"""
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class ScheduledJob:
    """스케줄된 작업"""
    job_id: str
    name: str
    schedule_type: ScheduleType
    schedule_config: Dict[str, Any]
    action: Callable
    action_args: Dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.SCHEDULED
    created_at: datetime = field(default_factory=datetime.utcnow)
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    max_retries: int = 3
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "job_id": self.job_id,
            "name": self.name,
            "schedule_type": self.schedule_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "enabled": self.enabled
        }


class ScheduleCalculator:
    """스케줄 시간 계산기"""
    
    @staticmethod
    def calculate_next_run(
        schedule_type: ScheduleType,
        config: Dict[str, Any],
        last_run: Optional[datetime] = None
    ) -> Optional[datetime]:
        """다음 실행 시간 계산"""
        now = datetime.utcnow()
        base_time = last_run or now
        
        if schedule_type == ScheduleType.ONCE:
            # 한 번만 실행
            run_at = config.get("run_at")
            if isinstance(run_at, str):
                run_at = datetime.fromisoformat(run_at)
            return run_at if run_at > now else None
        
        elif schedule_type == ScheduleType.INTERVAL:
            # 주기적 실행
            interval = config.get("interval", 3600)  # 기본 1시간
            if isinstance(interval, timedelta):
                return base_time + interval
            else:
                return base_time + timedelta(seconds=interval)
        
        elif schedule_type == ScheduleType.CRON:
            # Cron 표현식
            cron_expr = config.get("cron", "0 * * * *")  # 기본 매시간
            cron = croniter.croniter(cron_expr, base_time)
            return cron.get_next(datetime)
        
        elif schedule_type == ScheduleType.DAILY:
            # 매일 특정 시간
            hour = config.get("hour", 0)
            minute = config.get("minute", 0)
            next_run = base_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= base_time:
                next_run += timedelta(days=1)
            return next_run
        
        elif schedule_type == ScheduleType.WEEKLY:
            # 매주 특정 요일
            weekday = config.get("weekday", 0)  # 0=월요일
            hour = config.get("hour", 0)
            minute = config.get("minute", 0)
            
            days_ahead = weekday - base_time.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            
            next_run = base_time + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return next_run
        
        elif schedule_type == ScheduleType.MONTHLY:
            # 매월 특정 날짜
            day = config.get("day", 1)
            hour = config.get("hour", 0)
            minute = config.get("minute", 0)
            
            next_run = base_time.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= base_time:
                # 다음 달로
                if base_time.month == 12:
                    next_run = next_run.replace(year=base_time.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=base_time.month + 1)
            return next_run
        
        return None


class TaskScheduler:
    """
    작업 스케줄러
    
    시간 기반 작업 실행 관리
    """
    
    def __init__(self):
        self.jobs: Dict[str, ScheduledJob] = {}
        self.running_jobs: Dict[str, asyncio.Task] = {}
        self.scheduler_task: Optional[asyncio.Task] = None
        self._running = False
        self.job_callbacks: List[Callable] = []
        self.calculator = ScheduleCalculator()
        self.logger = logger
    
    async def start(self):
        """스케줄러 시작"""
        if self._running:
            self.logger.warning("Scheduler already running")
            return
        
        self._running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("Scheduler started")
    
    async def stop(self):
        """스케줄러 중지"""
        self._running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        # 실행 중인 작업 취소
        for task in self.running_jobs.values():
            task.cancel()
        
        await asyncio.gather(*self.running_jobs.values(), return_exceptions=True)
        self.running_jobs.clear()
        
        self.logger.info("Scheduler stopped")
    
    async def _scheduler_loop(self):
        """스케줄러 메인 루프"""
        while self._running:
            try:
                now = datetime.utcnow()
                
                # 실행할 작업 확인
                for job_id, job in self.jobs.items():
                    if not job.enabled or job.status == JobStatus.PAUSED:
                        continue
                    
                    if job.next_run and job.next_run <= now:
                        # 이미 실행 중이 아니면 실행
                        if job_id not in self.running_jobs:
                            task = asyncio.create_task(self._execute_job(job))
                            self.running_jobs[job_id] = task
                
                # 1초 대기
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(5)
    
    async def _execute_job(self, job: ScheduledJob):
        """작업 실행"""
        job.status = JobStatus.RUNNING
        job.last_run = datetime.utcnow()
        
        try:
            self.logger.info(f"Executing scheduled job: {job.name}")
            
            # 액션 실행
            if asyncio.iscoroutinefunction(job.action):
                result = await job.action(**job.action_args)
            else:
                result = await asyncio.to_thread(job.action, **job.action_args)
            
            # 성공
            job.status = JobStatus.COMPLETED
            job.run_count += 1
            
            # 콜백 실행
            await self._run_callbacks(job, result, None)
            
            # 다음 실행 시간 계산
            if job.schedule_type != ScheduleType.ONCE:
                job.next_run = self.calculator.calculate_next_run(
                    job.schedule_type,
                    job.schedule_config,
                    job.last_run
                )
                job.status = JobStatus.SCHEDULED
            
        except Exception as e:
            self.logger.error(f"Job {job.name} failed: {e}")
            job.status = JobStatus.FAILED
            job.error_count += 1
            
            # 콜백 실행
            await self._run_callbacks(job, None, e)
            
            # 재시도 처리
            if job.error_count <= job.max_retries:
                # 백오프와 함께 다시 스케줄
                retry_delay = 2 ** job.error_count  # 지수 백오프
                job.next_run = datetime.utcnow() + timedelta(seconds=retry_delay)
                job.status = JobStatus.SCHEDULED
                self.logger.info(f"Rescheduling job {job.name} after {retry_delay} seconds")
            
        finally:
            # 실행 중 작업에서 제거
            if job.job_id in self.running_jobs:
                del self.running_jobs[job.job_id]
    
    async def _run_callbacks(
        self,
        job: ScheduledJob,
        result: Any,
        error: Optional[Exception]
    ):
        """콜백 실행"""
        for callback in self.job_callbacks:
            try:
                await callback(job, result, error)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")
    
    def schedule_once(
        self,
        name: str,
        action: Callable,
        run_at: Union[datetime, str],
        action_args: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """한 번만 실행할 작업 스케줄"""
        if isinstance(run_at, str):
            run_at = datetime.fromisoformat(run_at)
        
        job_id = str(uuid.uuid4())
        job = ScheduledJob(
            job_id=job_id,
            name=name,
            schedule_type=ScheduleType.ONCE,
            schedule_config={"run_at": run_at},
            action=action,
            action_args=action_args or {},
            next_run=run_at,
            metadata=metadata or {}
        )
        
        self.jobs[job_id] = job
        self.logger.info(f"Scheduled once job: {name} at {run_at}")
        
        return job_id
    
    def schedule_interval(
        self,
        name: str,
        action: Callable,
        interval: Union[int, timedelta],
        action_args: Dict[str, Any] = None,
        start_immediately: bool = False,
        metadata: Dict[str, Any] = None
    ) -> str:
        """주기적으로 실행할 작업 스케줄"""
        if isinstance(interval, int):
            interval = timedelta(seconds=interval)
        
        job_id = str(uuid.uuid4())
        
        # 다음 실행 시간
        if start_immediately:
            next_run = datetime.utcnow()
        else:
            next_run = datetime.utcnow() + interval
        
        job = ScheduledJob(
            job_id=job_id,
            name=name,
            schedule_type=ScheduleType.INTERVAL,
            schedule_config={"interval": interval},
            action=action,
            action_args=action_args or {},
            next_run=next_run,
            metadata=metadata or {}
        )
        
        self.jobs[job_id] = job
        self.logger.info(f"Scheduled interval job: {name} every {interval}")
        
        return job_id
    
    def schedule_cron(
        self,
        name: str,
        action: Callable,
        cron_expr: str,
        action_args: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Cron 표현식으로 작업 스케줄"""
        job_id = str(uuid.uuid4())
        
        # 다음 실행 시간 계산
        next_run = self.calculator.calculate_next_run(
            ScheduleType.CRON,
            {"cron": cron_expr}
        )
        
        job = ScheduledJob(
            job_id=job_id,
            name=name,
            schedule_type=ScheduleType.CRON,
            schedule_config={"cron": cron_expr},
            action=action,
            action_args=action_args or {},
            next_run=next_run,
            metadata=metadata or {}
        )
        
        self.jobs[job_id] = job
        self.logger.info(f"Scheduled cron job: {name} with expression {cron_expr}")
        
        return job_id
    
    def schedule_daily(
        self,
        name: str,
        action: Callable,
        hour: int,
        minute: int = 0,
        action_args: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """매일 특정 시간에 실행할 작업 스케줄"""
        job_id = str(uuid.uuid4())
        
        # 다음 실행 시간 계산
        next_run = self.calculator.calculate_next_run(
            ScheduleType.DAILY,
            {"hour": hour, "minute": minute}
        )
        
        job = ScheduledJob(
            job_id=job_id,
            name=name,
            schedule_type=ScheduleType.DAILY,
            schedule_config={"hour": hour, "minute": minute},
            action=action,
            action_args=action_args or {},
            next_run=next_run,
            metadata=metadata or {}
        )
        
        self.jobs[job_id] = job
        self.logger.info(f"Scheduled daily job: {name} at {hour:02d}:{minute:02d}")
        
        return job_id
    
    def cancel_job(self, job_id: str) -> bool:
        """작업 취소"""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            job.status = JobStatus.CANCELLED
            job.enabled = False
            
            # 실행 중이면 취소
            if job_id in self.running_jobs:
                self.running_jobs[job_id].cancel()
            
            self.logger.info(f"Cancelled job: {job.name}")
            return True
        
        return False
    
    def pause_job(self, job_id: str) -> bool:
        """작업 일시정지"""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            job.status = JobStatus.PAUSED
            job.enabled = False
            self.logger.info(f"Paused job: {job.name}")
            return True
        
        return False
    
    def resume_job(self, job_id: str) -> bool:
        """작업 재개"""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            job.status = JobStatus.SCHEDULED
            job.enabled = True
            
            # 다음 실행 시간 재계산
            job.next_run = self.calculator.calculate_next_run(
                job.schedule_type,
                job.schedule_config,
                job.last_run
            )
            
            self.logger.info(f"Resumed job: {job.name}")
            return True
        
        return False
    
    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        """작업 조회"""
        return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> List[ScheduledJob]:
        """모든 작업 조회"""
        return list(self.jobs.values())
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """작업 상태 조회"""
        job = self.jobs.get(job_id)
        if job:
            return job.to_dict()
        return None
    
    def register_callback(self, callback: Callable):
        """작업 완료 콜백 등록"""
        self.job_callbacks.append(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 조회"""
        total = len(self.jobs)
        running = len(self.running_jobs)
        scheduled = sum(1 for j in self.jobs.values() if j.status == JobStatus.SCHEDULED)
        failed = sum(1 for j in self.jobs.values() if j.status == JobStatus.FAILED)
        
        return {
            "total_jobs": total,
            "running_jobs": running,
            "scheduled_jobs": scheduled,
            "failed_jobs": failed,
            "enabled_jobs": sum(1 for j in self.jobs.values() if j.enabled),
            "total_runs": sum(j.run_count for j in self.jobs.values()),
            "total_errors": sum(j.error_count for j in self.jobs.values())
        }
