"""
데이터베이스 리포지토리
비즈니스 로직을 위한 데이터 접근 계층
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import hashlib
import json

from .models import (
    Task,
    ScrapeResult,
    AnalysisResult,
    MonitoringConfig,
    ChangeEvent,
    Template,
    WorkflowExecution,
    ScheduledJob
)


class BaseRepository:
    """베이스 리포지토리"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def commit(self):
        """변경사항 커밋"""
        self.db.commit()
    
    def rollback(self):
        """변경사항 롤백"""
        self.db.rollback()


class TaskRepository(BaseRepository):
    """작업 리포지토리"""
    
    def create(
        self,
        task_type: str,
        status: str = "pending",
        priority: str = "medium",
        config: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> Task:
        """작업 생성"""
        task = Task(
            task_type=task_type,
            status=status,
            priority=priority,
            config=config or {},
            metadata=metadata or {}
        )
        self.db.add(task)
        self.db.commit()
        return task
    
    def get(self, task_id: str) -> Optional[Task]:
        """작업 조회"""
        return self.db.query(Task).filter(Task.id == task_id).first()
    
    def get_by_status(self, status: str, limit: int = 100) -> List[Task]:
        """상태별 작업 조회"""
        return self.db.query(Task)\
            .filter(Task.status == status)\
            .order_by(Task.created_at.desc())\
            .limit(limit)\
            .all()
    
    def update_status(
        self,
        task_id: str,
        status: str,
        result: Dict[str, Any] = None,
        error: str = None
    ) -> Optional[Task]:
        """작업 상태 업데이트"""
        task = self.get(task_id)
        if task:
            task.status = status
            
            if status == "running" and not task.started_at:
                task.started_at = datetime.utcnow()
            elif status in ["completed", "failed"]:
                task.completed_at = datetime.utcnow()
            
            if result:
                task.result = result
            
            if error:
                task.error = error
                task.retry_count += 1
            
            self.db.commit()
        
        return task
    
    def get_pending_tasks(self, limit: int = 10) -> List[Task]:
        """대기 중인 작업 조회"""
        return self.db.query(Task)\
            .filter(Task.status == "pending")\
            .order_by(Task.created_at)\
            .limit(limit)\
            .all()
    
    def get_recent_tasks(self, hours: int = 24, limit: int = 100) -> List[Task]:
        """최근 작업 조회"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(Task)\
            .filter(Task.created_at >= cutoff)\
            .order_by(Task.created_at.desc())\
            .limit(limit)\
            .all()
    
    def cleanup_old_tasks(self, days: int = 30) -> int:
        """오래된 작업 정리"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        count = self.db.query(Task)\
            .filter(Task.created_at < cutoff)\
            .delete()
        self.db.commit()
        return count


class ScrapeRepository(BaseRepository):
    """스크래핑 결과 리포지토리"""
    
    def create(
        self,
        task_id: str,
        url: str,
        strategy: str,
        success: bool,
        data: Dict[str, Any],
        execution_time: float = 0.0,
        metadata: Dict[str, Any] = None
    ) -> ScrapeResult:
        """스크래핑 결과 생성"""
        result = ScrapeResult(
            task_id=task_id,
            url=url,
            strategy=strategy,
            success=success,
            data=data,
            execution_time=execution_time,
            metadata=metadata or {}
        )
        self.db.add(result)
        self.db.commit()
        return result
    
    def get(self, result_id: str) -> Optional[ScrapeResult]:
        """결과 조회"""
        return self.db.query(ScrapeResult)\
            .filter(ScrapeResult.id == result_id)\
            .first()
    
    def get_by_url(self, url: str, limit: int = 10) -> List[ScrapeResult]:
        """URL별 결과 조회"""
        return self.db.query(ScrapeResult)\
            .filter(ScrapeResult.url == url)\
            .order_by(ScrapeResult.created_at.desc())\
            .limit(limit)\
            .all()
    
    def get_recent_successful(self, hours: int = 24) -> List[ScrapeResult]:
        """최근 성공한 스크래핑 조회"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(ScrapeResult)\
            .filter(and_(
                ScrapeResult.created_at >= cutoff,
                ScrapeResult.success == True
            ))\
            .order_by(ScrapeResult.created_at.desc())\
            .all()


class AnalysisRepository(BaseRepository):
    """분석 결과 리포지토리"""
    
    def create(
        self,
        content: str,
        analysis_type: str,
        result: Dict[str, Any],
        confidence: float = 0.0,
        language: str = "ko",
        metadata: Dict[str, Any] = None
    ) -> AnalysisResult:
        """분석 결과 생성"""
        # 콘텐츠 해시 생성
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        analysis = AnalysisResult(
            content_hash=content_hash,
            analysis_type=analysis_type,
            result=result,
            confidence=confidence,
            language=language,
            metadata=metadata or {}
        )
        self.db.add(analysis)
        self.db.commit()
        return analysis
    
    def get_by_content_hash(
        self,
        content_hash: str,
        analysis_type: str
    ) -> Optional[AnalysisResult]:
        """콘텐츠 해시로 조회"""
        return self.db.query(AnalysisResult)\
            .filter(and_(
                AnalysisResult.content_hash == content_hash,
                AnalysisResult.analysis_type == analysis_type
            ))\
            .first()
    
    def get_cached_analysis(
        self,
        content: str,
        analysis_type: str,
        max_age_hours: int = 24
    ) -> Optional[AnalysisResult]:
        """캐시된 분석 결과 조회"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        return self.db.query(AnalysisResult)\
            .filter(and_(
                AnalysisResult.content_hash == content_hash,
                AnalysisResult.analysis_type == analysis_type,
                AnalysisResult.created_at >= cutoff
            ))\
            .first()
    
    def get_by_type(
        self,
        analysis_type: str,
        limit: int = 100
    ) -> List[AnalysisResult]:
        """타입별 분석 결과 조회"""
        return self.db.query(AnalysisResult)\
            .filter(AnalysisResult.analysis_type == analysis_type)\
            .order_by(AnalysisResult.created_at.desc())\
            .limit(limit)\
            .all()


class MonitoringRepository(BaseRepository):
    """모니터링 설정 리포지토리"""
    
    def create(
        self,
        url: str,
        strategy: str,
        keywords: List[str] = None,
        check_interval_minutes: int = 60,
        notification_threshold: float = 0.3,
        ai_analysis: bool = True,
        metadata: Dict[str, Any] = None
    ) -> MonitoringConfig:
        """모니터링 설정 생성"""
        config = MonitoringConfig(
            url=url,
            strategy=strategy,
            keywords=keywords or [],
            check_interval_minutes=check_interval_minutes,
            notification_threshold=notification_threshold,
            ai_analysis=ai_analysis,
            metadata=metadata or {}
        )
        
        # 다음 체크 시간 설정
        config.next_check = datetime.utcnow() + timedelta(minutes=check_interval_minutes)
        
        self.db.add(config)
        self.db.commit()
        return config
    
    def get(self, monitoring_id: str) -> Optional[MonitoringConfig]:
        """모니터링 설정 조회"""
        return self.db.query(MonitoringConfig)\
            .filter(MonitoringConfig.id == monitoring_id)\
            .first()
    
    def get_active(self) -> List[MonitoringConfig]:
        """활성 모니터링 조회"""
        return self.db.query(MonitoringConfig)\
            .filter(MonitoringConfig.is_active == True)\
            .all()
    
    def get_due_for_check(self) -> List[MonitoringConfig]:
        """체크 대상 모니터링 조회"""
        now = datetime.utcnow()
        return self.db.query(MonitoringConfig)\
            .filter(and_(
                MonitoringConfig.is_active == True,
                or_(
                    MonitoringConfig.next_check <= now,
                    MonitoringConfig.next_check == None
                )
            ))\
            .all()
    
    def update_check_time(
        self,
        monitoring_id: str,
        success: bool = True
    ) -> Optional[MonitoringConfig]:
        """체크 시간 업데이트"""
        config = self.get(monitoring_id)
        if config:
            config.last_check = datetime.utcnow()
            config.next_check = datetime.utcnow() + timedelta(
                minutes=config.check_interval_minutes
            )
            config.updated_at = datetime.utcnow()
            
            self.db.commit()
        
        return config
    
    def deactivate(self, monitoring_id: str) -> bool:
        """모니터링 비활성화"""
        config = self.get(monitoring_id)
        if config:
            config.is_active = False
            config.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def add_change_event(
        self,
        monitoring_id: str,
        change_type: str,
        importance_score: float,
        change_summary: str,
        notification_priority: str = "low",
        diff_details: Dict[str, Any] = None,
        ai_analysis: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> ChangeEvent:
        """변경 이벤트 추가"""
        config = self.get(monitoring_id)
        if not config:
            raise ValueError(f"Monitoring {monitoring_id} not found")
        
        event = ChangeEvent(
            monitoring_id=monitoring_id,
            url=config.url,
            change_type=change_type,
            importance_score=importance_score,
            change_summary=change_summary,
            notification_priority=notification_priority,
            diff_details=diff_details or {},
            ai_analysis=ai_analysis or {},
            metadata=metadata or {}
        )
        
        self.db.add(event)
        self.db.commit()
        return event
    
    def get_change_events(
        self,
        monitoring_id: str,
        limit: int = 100
    ) -> List[ChangeEvent]:
        """변경 이벤트 조회"""
        return self.db.query(ChangeEvent)\
            .filter(ChangeEvent.monitoring_id == monitoring_id)\
            .order_by(ChangeEvent.created_at.desc())\
            .limit(limit)\
            .all()


class TemplateRepository(BaseRepository):
    """템플릿 리포지토리"""
    
    def create(
        self,
        template_id: str,
        domain: str,
        url_pattern: str,
        selectors: Dict[str, Any],
        confidence: float = 0.0,
        metadata: Dict[str, Any] = None
    ) -> Template:
        """템플릿 생성"""
        template = Template(
            template_id=template_id,
            domain=domain,
            url_pattern=url_pattern,
            selectors=selectors,
            confidence=confidence,
            metadata=metadata or {}
        )
        self.db.add(template)
        self.db.commit()
        return template
    
    def get_by_template_id(self, template_id: str) -> Optional[Template]:
        """템플릿 ID로 조회"""
        return self.db.query(Template)\
            .filter(Template.template_id == template_id)\
            .first()
    
    def get_by_domain(self, domain: str) -> List[Template]:
        """도메인별 템플릿 조회"""
        return self.db.query(Template)\
            .filter(Template.domain == domain)\
            .order_by(Template.confidence.desc())\
            .all()
    
    def get_best_template(self, domain: str) -> Optional[Template]:
        """최적 템플릿 조회"""
        return self.db.query(Template)\
            .filter(Template.domain == domain)\
            .order_by(Template.confidence.desc(), Template.success_rate.desc())\
            .first()
    
    def update_usage(
        self,
        template_id: str,
        success: bool
    ) -> Optional[Template]:
        """템플릿 사용 업데이트"""
        template = self.get_by_template_id(template_id)
        if template:
            template.usage_count += 1
            
            # 성공률 업데이트
            if template.usage_count == 1:
                template.success_rate = 1.0 if success else 0.0
            else:
                # 이동 평균
                template.success_rate = (
                    template.success_rate * (template.usage_count - 1) +
                    (1.0 if success else 0.0)
                ) / template.usage_count
            
            template.updated_at = datetime.utcnow()
            self.db.commit()
        
        return template
    
    def cleanup_low_performing(
        self,
        min_confidence: float = 0.3,
        min_success_rate: float = 0.5
    ) -> int:
        """성능이 낮은 템플릿 정리"""
        count = self.db.query(Template)\
            .filter(or_(
                Template.confidence < min_confidence,
                and_(
                    Template.usage_count > 10,
                    Template.success_rate < min_success_rate
                )
            ))\
            .delete()
        self.db.commit()
        return count
