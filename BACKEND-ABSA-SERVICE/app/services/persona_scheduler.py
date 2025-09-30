"""
Persona Batch Recalculation Scheduler

페르소나 배치 재계산 스케줄러:
- Stale 페르소나 자동 감지
- 우선순위 기반 스케줄링
- 배치 작업 큐 관리
- 진행 상황 추적
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from enum import Enum

# Celery/RQ 작업 큐 (선택적 의존성)
try:
    from celery import Celery, Task
    from celery.result import AsyncResult
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """배치 작업 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchJob:
    """배치 작업 정보"""
    job_id: str
    status: JobStatus
    total_personas: int
    processed: int
    succeeded: int
    failed: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str] = None


@dataclass
class PersonaRecalcResult:
    """페르소나 재계산 결과"""
    persona_id: int
    user_id: str
    success: bool
    updated_fields: List[str]
    error_message: Optional[str] = None
    duration_seconds: float = 0.0


class PersonaScheduler:
    """페르소나 배치 재계산 스케줄러"""
    
    # Stale 기준 (24시간)
    STALE_THRESHOLD_HOURS = 24
    
    # 배치 크기
    DEFAULT_BATCH_SIZE = 50
    MAX_BATCH_SIZE = 200
    
    def __init__(self, db: Session, celery_app: Optional[Any] = None):
        """
        초기화
        
        Args:
            db: 데이터베이스 세션
            celery_app: Celery 앱 인스턴스 (선택)
        """
        self.db = db
        self.celery_app = celery_app
        self.active_jobs: Dict[str, BatchJob] = {}
    
    def find_stale_personas(
        self,
        threshold_hours: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Stale 페르소나 검색
        
        Args:
            threshold_hours: Stale 기준 시간 (기본: 24시간)
            
        Returns:
            Stale 페르소나 목록
        """
        if threshold_hours is None:
            threshold_hours = self.STALE_THRESHOLD_HOURS
        
        cutoff_time = datetime.now() - timedelta(hours=threshold_hours)
        
        # 실제 구현에서는 DB 쿼리
        # Example: 
        # stale_personas = self.db.query(UserPersona).filter(
        #     UserPersona.last_calculated_at < cutoff_time
        # ).all()
        
        # 현재는 시뮬레이션
        logger.info(f"Stale 페르소나 검색: {threshold_hours}시간 이상 업데이트 안됨")
        
        # TODO: 실제 DB 연동
        return []
    
    def calculate_priority(self, persona: Dict[str, Any]) -> int:
        """
        페르소나 재계산 우선순위 계산
        
        우선순위 기준:
        1. 영향력 높음 (높은 우선순위)
        2. 최근 활동 많음 (높은 우선순위)
        3. 오래된 업데이트 (높은 우선순위)
        
        Args:
            persona: 페르소나 정보
            
        Returns:
            우선순위 점수 (높을수록 우선)
        """
        priority = 0
        
        # 영향력 점수 반영 (0-50점)
        influence = persona.get('influence_score', 0)
        priority += min(influence / 2, 50)
        
        # 최근 활동 반영 (0-30점)
        recent_activity_count = persona.get('recent_activity_count', 0)
        priority += min(recent_activity_count, 30)
        
        # 업데이트 오래됨 반영 (0-20점)
        last_updated = persona.get('last_calculated_at')
        if last_updated:
            hours_since_update = (datetime.now() - last_updated).total_seconds() / 3600
            priority += min(hours_since_update / 24 * 20, 20)
        
        return int(priority)
    
    async def schedule_batch_recalculation(
        self,
        persona_ids: Optional[List[int]] = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        priority_filter: Optional[int] = None
    ) -> BatchJob:
        """
        배치 재계산 스케줄
        
        Args:
            persona_ids: 특정 페르소나 ID 목록 (None이면 모든 stale 페르소나)
            batch_size: 배치 크기
            priority_filter: 우선순위 필터 (이 값 이상만 처리)
            
        Returns:
            BatchJob: 배치 작업 정보
        """
        import uuid
        
        job_id = str(uuid.uuid4())
        
        # Stale 페르소나 찾기
        if persona_ids is None:
            stale_personas = self.find_stale_personas()
            persona_ids = [p['id'] for p in stale_personas]
        
        # 우선순위 필터링
        if priority_filter:
            # TODO: 우선순위 계산 및 필터링
            pass
        
        batch_size = min(batch_size, self.MAX_BATCH_SIZE)
        
        # 배치 작업 생성
        batch_job = BatchJob(
            job_id=job_id,
            status=JobStatus.PENDING,
            total_personas=len(persona_ids),
            processed=0,
            succeeded=0,
            failed=0,
            started_at=None,
            completed_at=None
        )
        
        self.active_jobs[job_id] = batch_job
        
        # Celery 사용 가능하면 비동기 작업 등록
        if CELERY_AVAILABLE and self.celery_app:
            task = self._submit_celery_task(job_id, persona_ids, batch_size)
            logger.info(f"Celery 작업 등록: {task.id}")
        else:
            # Fallback: 동기 처리
            logger.warning("Celery 미사용 - 동기 처리 모드")
            await self._execute_batch_sync(job_id, persona_ids, batch_size)
        
        return batch_job
    
    def _submit_celery_task(
        self,
        job_id: str,
        persona_ids: List[int],
        batch_size: int
    ) -> Any:
        """
        Celery 작업 제출
        
        Args:
            job_id: 작업 ID
            persona_ids: 페르소나 ID 목록
            batch_size: 배치 크기
            
        Returns:
            Celery AsyncResult
        """
        # Celery 태스크 정의 (실제 구현에서는 별도 파일)
        @self.celery_app.task(bind=True)
        def recalculate_personas_task(self, job_id, persona_ids, batch_size):
            return self._execute_batch_sync(job_id, persona_ids, batch_size)
        
        return recalculate_personas_task.delay(job_id, persona_ids, batch_size)
    
    async def _execute_batch_sync(
        self,
        job_id: str,
        persona_ids: List[int],
        batch_size: int
    ) -> BatchJob:
        """
        배치 재계산 동기 실행
        
        Args:
            job_id: 작업 ID
            persona_ids: 페르소나 ID 목록
            batch_size: 배치 크기
            
        Returns:
            BatchJob: 완료된 작업 정보
        """
        batch_job = self.active_jobs.get(job_id)
        if not batch_job:
            raise ValueError(f"작업을 찾을 수 없습니다: {job_id}")
        
        batch_job.status = JobStatus.RUNNING
        batch_job.started_at = datetime.now()
        
        logger.info(f"배치 재계산 시작: {len(persona_ids)}개 페르소나")
        
        results: List[PersonaRecalcResult] = []
        
        # 배치 단위로 처리
        for i in range(0, len(persona_ids), batch_size):
            batch = persona_ids[i:i + batch_size]
            
            for persona_id in batch:
                try:
                    result = await self._recalculate_persona(persona_id)
                    results.append(result)
                    
                    if result.success:
                        batch_job.succeeded += 1
                    else:
                        batch_job.failed += 1
                    
                except Exception as e:
                    logger.error(f"페르소나 {persona_id} 재계산 실패: {e}")
                    batch_job.failed += 1
                    results.append(PersonaRecalcResult(
                        persona_id=persona_id,
                        user_id="unknown",
                        success=False,
                        updated_fields=[],
                        error_message=str(e)
                    ))
                
                batch_job.processed += 1
            
            # 진행 상황 로깅
            progress = (batch_job.processed / batch_job.total_personas) * 100
            logger.info(f"진행률: {progress:.1f}% ({batch_job.processed}/{batch_job.total_personas})")
        
        # 작업 완료
        batch_job.status = JobStatus.COMPLETED
        batch_job.completed_at = datetime.now()
        
        duration = (batch_job.completed_at - batch_job.started_at).total_seconds()
        logger.info(
            f"배치 재계산 완료: {batch_job.succeeded}개 성공, "
            f"{batch_job.failed}개 실패 (소요시간: {duration:.1f}초)"
        )
        
        return batch_job
    
    async def _recalculate_persona(self, persona_id: int) -> PersonaRecalcResult:
        """
        단일 페르소나 재계산
        
        Args:
            persona_id: 페르소나 ID
            
        Returns:
            PersonaRecalcResult: 재계산 결과
        """
        start_time = datetime.now()
        
        try:
            # TODO: 실제 페르소나 재계산 로직
            # 1. 페르소나 조회
            # 2. 최근 활동 데이터 수집
            # 3. 감정 패턴 재분석
            # 4. 영향력 점수 재계산
            # 5. DB 업데이트
            
            # 시뮬레이션
            updated_fields = [
                'emotion_distribution',
                'influence_score',
                'activity_count',
                'last_calculated_at'
            ]
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return PersonaRecalcResult(
                persona_id=persona_id,
                user_id=f"user_{persona_id}",
                success=True,
                updated_fields=updated_fields,
                duration_seconds=duration
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return PersonaRecalcResult(
                persona_id=persona_id,
                user_id="unknown",
                success=False,
                updated_fields=[],
                error_message=str(e),
                duration_seconds=duration
            )
    
    async def recalculate_all_stale(
        self,
        batch_size: int = DEFAULT_BATCH_SIZE,
        min_priority: int = 50
    ) -> BatchJob:
        """
        모든 Stale 페르소나 재계산
        
        Args:
            batch_size: 배치 크기
            min_priority: 최소 우선순위 (이 값 이상만 처리)
            
        Returns:
            BatchJob: 배치 작업 정보
        """
        stale_personas = self.find_stale_personas()
        
        # 우선순위 계산 및 필터링
        personas_with_priority = [
            (persona, self.calculate_priority(persona))
            for persona in stale_personas
        ]
        
        # 우선순위 필터링
        filtered = [
            persona for persona, priority in personas_with_priority
            if priority >= min_priority
        ]
        
        # 우선순위 정렬 (높은 순)
        filtered.sort(
            key=lambda p: self.calculate_priority(p),
            reverse=True
        )
        
        persona_ids = [p['id'] for p in filtered]
        
        logger.info(
            f"Stale 페르소나 {len(stale_personas)}개 중 "
            f"{len(filtered)}개 선택 (우선순위 >= {min_priority})"
        )
        
        return await self.schedule_batch_recalculation(
            persona_ids=persona_ids,
            batch_size=batch_size
        )
    
    def get_job_status(self, job_id: str) -> Optional[BatchJob]:
        """
        작업 상태 조회
        
        Args:
            job_id: 작업 ID
            
        Returns:
            BatchJob: 작업 정보 (없으면 None)
        """
        return self.active_jobs.get(job_id)
    
    def cancel_job(self, job_id: str) -> bool:
        """
        작업 취소
        
        Args:
            job_id: 작업 ID
            
        Returns:
            성공 여부
        """
        batch_job = self.active_jobs.get(job_id)
        if not batch_job:
            return False
        
        if batch_job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            logger.warning(f"이미 완료/실패/취소된 작업입니다: {job_id}")
            return False
        
        batch_job.status = JobStatus.CANCELLED
        batch_job.completed_at = datetime.now()
        
        # Celery 작업 취소
        if CELERY_AVAILABLE and self.celery_app:
            # TODO: Celery 작업 취소 구현
            pass
        
        logger.info(f"작업 취소: {job_id}")
        return True
    
    def get_all_jobs(self) -> List[BatchJob]:
        """
        모든 작업 조회
        
        Returns:
            작업 목록
        """
        return list(self.active_jobs.values())
    
    def cleanup_old_jobs(self, days: int = 7) -> int:
        """
        오래된 작업 정리
        
        Args:
            days: 보관 기간 (일)
            
        Returns:
            정리된 작업 수
        """
        cutoff = datetime.now() - timedelta(days=days)
        cleaned = 0
        
        job_ids_to_remove = []
        for job_id, job in self.active_jobs.items():
            if job.completed_at and job.completed_at < cutoff:
                job_ids_to_remove.append(job_id)
        
        for job_id in job_ids_to_remove:
            del self.active_jobs[job_id]
            cleaned += 1
        
        logger.info(f"{cleaned}개 오래된 작업 정리 완료")
        return cleaned
