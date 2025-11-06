"""
상태 관리 시스템
작업 및 시스템 상태 추적 및 관리
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)


class StateType(Enum):
    """상태 타입"""
    TASK = "task"
    WORKFLOW = "workflow"
    MONITORING = "monitoring"
    SYSTEM = "system"
    CACHE = "cache"


class PersistenceMode(Enum):
    """지속성 모드"""
    MEMORY = "memory"  # 메모리만
    FILE = "file"  # 파일 저장
    REDIS = "redis"  # Redis 저장
    DATABASE = "database"  # 데이터베이스


@dataclass
class TaskState:
    """작업 상태"""
    task_id: str
    task_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
            "metadata": self.metadata
        }


@dataclass
class SystemState:
    """시스템 상태"""
    component: str
    status: str
    health: str
    metrics: Dict[str, Any]
    last_heartbeat: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "component": self.component,
            "status": self.status,
            "health": self.health,
            "metrics": self.metrics,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "metadata": self.metadata
        }


class StateStore:
    """상태 저장소 인터페이스"""
    
    async def get(self, key: str) -> Optional[Any]:
        """상태 조회"""
        raise NotImplementedError
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """상태 저장"""
        raise NotImplementedError
    
    async def delete(self, key: str):
        """상태 삭제"""
        raise NotImplementedError
    
    async def exists(self, key: str) -> bool:
        """상태 존재 여부"""
        raise NotImplementedError
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """키 목록"""
        raise NotImplementedError


class MemoryStateStore(StateStore):
    """메모리 상태 저장소"""
    
    def __init__(self):
        self.store: Dict[str, Any] = {}
        self.ttl_store: Dict[str, datetime] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """상태 조회"""
        # TTL 체크
        if key in self.ttl_store:
            if datetime.utcnow() > self.ttl_store[key]:
                await self.delete(key)
                return None
        
        return self.store.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """상태 저장"""
        self.store[key] = value
        
        if ttl:
            self.ttl_store[key] = datetime.utcnow() + timedelta(seconds=ttl)
        elif key in self.ttl_store:
            del self.ttl_store[key]
    
    async def delete(self, key: str):
        """상태 삭제"""
        if key in self.store:
            del self.store[key]
        if key in self.ttl_store:
            del self.ttl_store[key]
    
    async def exists(self, key: str) -> bool:
        """상태 존재 여부"""
        return key in self.store
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """키 목록"""
        import fnmatch
        if pattern == "*":
            return list(self.store.keys())
        return [k for k in self.store.keys() if fnmatch.fnmatch(k, pattern)]


class FileStateStore(StateStore):
    """파일 기반 상태 저장소"""
    
    def __init__(self, base_path: str = "./state"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, key: str) -> Path:
        """파일 경로 생성"""
        # 키를 안전한 파일명으로 변환
        safe_key = key.replace("/", "_").replace(":", "_")
        return self.base_path / f"{safe_key}.state"
    
    async def get(self, key: str) -> Optional[Any]:
        """상태 조회"""
        file_path = self._get_file_path(key)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "rb") as f:
                data = pickle.load(f)
            
            # TTL 체크
            if "ttl" in data and datetime.utcnow() > data["ttl"]:
                await self.delete(key)
                return None
            
            return data.get("value")
            
        except Exception as e:
            logger.error(f"Failed to load state from {file_path}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """상태 저장"""
        file_path = self._get_file_path(key)
        
        data = {"value": value}
        if ttl:
            data["ttl"] = datetime.utcnow() + timedelta(seconds=ttl)
        
        try:
            with open(file_path, "wb") as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to save state to {file_path}: {e}")
    
    async def delete(self, key: str):
        """상태 삭제"""
        file_path = self._get_file_path(key)
        if file_path.exists():
            file_path.unlink()
    
    async def exists(self, key: str) -> bool:
        """상태 존재 여부"""
        return self._get_file_path(key).exists()
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """키 목록"""
        import fnmatch
        keys = []
        
        for file_path in self.base_path.glob("*.state"):
            key = file_path.stem.replace("_", ":")
            if pattern == "*" or fnmatch.fnmatch(key, pattern):
                keys.append(key)
        
        return keys


class StateManager:
    """
    상태 관리 시스템
    
    작업 및 시스템 상태 중앙 관리
    """
    
    def __init__(
        self,
        persistence_mode: PersistenceMode = PersistenceMode.MEMORY,
        **kwargs
    ):
        """
        초기화
        
        Args:
            persistence_mode: 지속성 모드
            **kwargs: 저장소별 추가 파라미터
        """
        self.persistence_mode = persistence_mode
        
        # 저장소 초기화
        if persistence_mode == PersistenceMode.MEMORY:
            self.store = MemoryStateStore()
        elif persistence_mode == PersistenceMode.FILE:
            base_path = kwargs.get("base_path", "./state")
            self.store = FileStateStore(base_path)
        else:
            # Redis나 DB는 추후 구현
            self.store = MemoryStateStore()
        
        # 상태 캐시
        self.task_states: Dict[str, TaskState] = {}
        self.system_states: Dict[str, SystemState] = {}
        
        # 상태 변경 리스너
        self.listeners: List[callable] = []
        
        # 통계
        self.statistics = {
            "state_updates": 0,
            "state_queries": 0,
            "state_deletes": 0
        }
        
        self.logger = logger
    
    async def save_task_state(self, task_state: TaskState):
        """작업 상태 저장"""
        key = f"task:{task_state.task_id}"
        task_state.updated_at = datetime.utcnow()
        
        await self.store.set(key, task_state)
        self.task_states[task_state.task_id] = task_state
        
        self.statistics["state_updates"] += 1
        
        # 리스너 알림
        await self._notify_listeners(StateType.TASK, task_state)
    
    async def get_task_state(self, task_id: str) -> Optional[TaskState]:
        """작업 상태 조회"""
        # 캐시 확인
        if task_id in self.task_states:
            self.statistics["state_queries"] += 1
            return self.task_states[task_id]
        
        # 저장소 조회
        key = f"task:{task_id}"
        state = await self.store.get(key)
        
        if state and isinstance(state, TaskState):
            self.task_states[task_id] = state
            self.statistics["state_queries"] += 1
            return state
        
        return None
    
    async def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ):
        """작업 상태 업데이트"""
        state = await self.get_task_state(task_id)
        
        if state:
            state.status = status
            state.updated_at = datetime.utcnow()
            
            if result is not None:
                state.result = result
            
            if error is not None:
                state.error = error
            
            if status == "running" and not state.started_at:
                state.started_at = datetime.utcnow()
            elif status in ["completed", "failed", "cancelled"]:
                state.completed_at = datetime.utcnow()
            
            await self.save_task_state(state)
    
    async def save_system_state(
        self,
        component: str,
        status: str,
        health: str,
        metrics: Dict[str, Any]
    ):
        """시스템 상태 저장"""
        system_state = SystemState(
            component=component,
            status=status,
            health=health,
            metrics=metrics,
            last_heartbeat=datetime.utcnow()
        )
        
        key = f"system:{component}"
        await self.store.set(key, system_state, ttl=300)  # 5분 TTL
        
        self.system_states[component] = system_state
        self.statistics["state_updates"] += 1
        
        # 리스너 알림
        await self._notify_listeners(StateType.SYSTEM, system_state)
    
    async def get_system_state(self, component: str) -> Optional[SystemState]:
        """시스템 상태 조회"""
        # 캐시 확인
        if component in self.system_states:
            state = self.system_states[component]
            # 하트비트 체크 (5분 이상 경과 시 stale)
            if datetime.utcnow() - state.last_heartbeat < timedelta(minutes=5):
                self.statistics["state_queries"] += 1
                return state
        
        # 저장소 조회
        key = f"system:{component}"
        state = await self.store.get(key)
        
        if state and isinstance(state, SystemState):
            self.system_states[component] = state
            self.statistics["state_queries"] += 1
            return state
        
        return None
    
    async def get_all_system_states(self) -> Dict[str, SystemState]:
        """모든 시스템 상태 조회"""
        states = {}
        
        keys = await self.store.keys("system:*")
        for key in keys:
            component = key.split(":", 1)[1]
            state = await self.get_system_state(component)
            if state:
                states[component] = state
        
        return states
    
    async def save_cache(
        self,
        cache_key: str,
        value: Any,
        ttl: int = 3600
    ):
        """캐시 저장"""
        key = f"cache:{cache_key}"
        await self.store.set(key, value, ttl=ttl)
        self.statistics["state_updates"] += 1
    
    async def get_cache(self, cache_key: str) -> Optional[Any]:
        """캐시 조회"""
        key = f"cache:{cache_key}"
        value = await self.store.get(key)
        
        if value is not None:
            self.statistics["state_queries"] += 1
        
        return value
    
    async def invalidate_cache(self, cache_key: str):
        """캐시 무효화"""
        key = f"cache:{cache_key}"
        await self.store.delete(key)
        self.statistics["state_deletes"] += 1
    
    async def cleanup_old_states(self, days: int = 7):
        """오래된 상태 정리"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 작업 상태 정리
        keys = await self.store.keys("task:*")
        for key in keys:
            state = await self.store.get(key)
            if isinstance(state, TaskState):
                if state.completed_at and state.completed_at < cutoff_date:
                    await self.store.delete(key)
                    task_id = key.split(":", 1)[1]
                    if task_id in self.task_states:
                        del self.task_states[task_id]
                    self.statistics["state_deletes"] += 1
    
    def add_listener(self, callback: callable):
        """상태 변경 리스너 추가"""
        self.listeners.append(callback)
    
    async def _notify_listeners(self, state_type: StateType, state: Any):
        """리스너 알림"""
        for listener in self.listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(state_type, state)
                else:
                    await asyncio.to_thread(listener, state_type, state)
            except Exception as e:
                self.logger.error(f"Listener error: {e}")
    
    async def export_state(self) -> Dict[str, Any]:
        """전체 상태 내보내기"""
        export_data = {
            "task_states": {},
            "system_states": {},
            "export_time": datetime.utcnow().isoformat()
        }
        
        # 작업 상태
        keys = await self.store.keys("task:*")
        for key in keys:
            state = await self.store.get(key)
            if isinstance(state, TaskState):
                export_data["task_states"][state.task_id] = state.to_dict()
        
        # 시스템 상태
        for component, state in self.system_states.items():
            export_data["system_states"][component] = state.to_dict()
        
        return export_data
    
    async def import_state(self, import_data: Dict[str, Any]):
        """상태 가져오기"""
        # 작업 상태
        for task_id, state_dict in import_data.get("task_states", {}).items():
            # TaskState 재구성
            state = TaskState(
                task_id=task_id,
                task_type=state_dict["task_type"],
                status=state_dict["status"],
                created_at=datetime.fromisoformat(state_dict["created_at"]),
                updated_at=datetime.fromisoformat(state_dict["updated_at"]),
                retry_count=state_dict.get("retry_count", 0),
                metadata=state_dict.get("metadata", {})
            )
            
            await self.save_task_state(state)
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 조회"""
        return {
            **self.statistics,
            "cached_tasks": len(self.task_states),
            "cached_systems": len(self.system_states),
            "persistence_mode": self.persistence_mode.value
        }
