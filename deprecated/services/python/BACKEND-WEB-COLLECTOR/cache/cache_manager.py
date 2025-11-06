"""
캐시 매니저
Redis 및 메모리 캐시 구현
"""
import os
import json
import pickle
import hashlib
import asyncio
import logging
from typing import Any, Optional, Union, Dict, List
from datetime import timedelta
from abc import ABC, abstractmethod
import time
from collections import OrderedDict
from threading import Lock

try:
    import redis
    from redis.asyncio import Redis as AsyncRedis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheManager(ABC):
    """캐시 매니저 베이스 클래스"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """값 조회"""
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """값 설정"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """값 삭제"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """키 존재 여부"""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """전체 캐시 초기화"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        pass
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """캐시 키 생성"""
        key_parts = [prefix]
        
        # 위치 인자 추가
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                # 복잡한 객체는 해시
                key_parts.append(hashlib.md5(
                    str(arg).encode()
                ).hexdigest()[:8])
        
        # 키워드 인자 추가
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (str, int, float, bool)):
                key_parts.append(f"{k}={v}")
            else:
                key_parts.append(f"{k}={hashlib.md5(str(v).encode()).hexdigest()[:8]}")
        
        return ":".join(key_parts)


class RedisCache(CacheManager):
    """Redis 캐시 구현"""
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 3600,
        max_connections: int = 50,
        decode_responses: bool = False
    ):
        """
        초기화
        
        Args:
            redis_url: Redis 연결 URL
            default_ttl: 기본 TTL (초)
            max_connections: 최대 연결 수
            decode_responses: 응답 디코딩 여부
        """
        if not REDIS_AVAILABLE:
            raise ImportError("redis package not installed")
        
        self.redis_url = redis_url or os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/0"
        )
        self.default_ttl = default_ttl
        
        # 연결 풀 생성
        self.pool = redis.asyncio.ConnectionPool.from_url(
            self.redis_url,
            max_connections=max_connections,
            decode_responses=decode_responses
        )
        self.redis = AsyncRedis(connection_pool=self.pool)
        
        # 통계
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
        
        logger.info(f"Redis cache initialized: {self._safe_url()}")
    
    def _safe_url(self) -> str:
        """안전한 URL 반환"""
        if "@" in self.redis_url:
            parts = self.redis_url.split("@")
            return parts[0].split("://")[0] + "://***@" + parts[1]
        return self.redis_url
    
    async def get(self, key: str) -> Optional[Any]:
        """값 조회"""
        try:
            value = await self.redis.get(key)
            
            if value is None:
                self.stats["misses"] += 1
                return None
            
            self.stats["hits"] += 1
            
            # 역직렬화
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                try:
                    return pickle.loads(value)
                except:
                    return value
                    
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            self.stats["errors"] += 1
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """값 설정"""
        try:
            # 직렬화
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            elif isinstance(value, (str, bytes)):
                serialized = value
            else:
                serialized = pickle.dumps(value)
            
            # TTL 설정
            ttl = ttl or self.default_ttl
            
            # Redis 저장
            result = await self.redis.setex(
                key,
                ttl,
                serialized
            )
            
            self.stats["sets"] += 1
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            self.stats["errors"] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """값 삭제"""
        try:
            result = await self.redis.delete(key)
            self.stats["deletes"] += 1
            return bool(result)
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            self.stats["errors"] += 1
            return False
    
    async def exists(self, key: str) -> bool:
        """키 존재 여부"""
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """전체 캐시 초기화"""
        try:
            await self.redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        try:
            info = await self.redis.info()
            return {
                **self.stats,
                "hit_rate": self.stats["hits"] / 
                           (self.stats["hits"] + self.stats["misses"])
                           if (self.stats["hits"] + self.stats["misses"]) > 0 else 0,
                "redis_info": {
                    "used_memory": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                    "total_commands": info.get("total_commands_processed"),
                    "keyspace": info.get("db0", {})
                }
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return self.stats
    
    async def close(self):
        """연결 종료"""
        await self.redis.close()
        await self.pool.disconnect()


class MemoryCache(CacheManager):
    """메모리 캐시 구현 (LRU)"""
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600
    ):
        """
        초기화
        
        Args:
            max_size: 최대 캐시 크기
            default_ttl: 기본 TTL (초)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict = OrderedDict()
        self.ttl_map: Dict[str, float] = {}
        self.lock = Lock()
        
        # 통계
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0
        }
        
        logger.info(f"Memory cache initialized with max_size={max_size}")
    
    async def get(self, key: str) -> Optional[Any]:
        """값 조회"""
        with self.lock:
            # TTL 체크
            if key in self.ttl_map:
                if time.time() > self.ttl_map[key]:
                    # 만료됨
                    del self.cache[key]
                    del self.ttl_map[key]
                    self.stats["misses"] += 1
                    return None
            
            # 캐시 조회
            if key in self.cache:
                # LRU 업데이트
                self.cache.move_to_end(key)
                self.stats["hits"] += 1
                return self.cache[key]
            
            self.stats["misses"] += 1
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """값 설정"""
        with self.lock:
            # 기존 키 제거
            if key in self.cache:
                del self.cache[key]
            
            # 크기 체크 및 제거
            while len(self.cache) >= self.max_size:
                # LRU 제거
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                if oldest_key in self.ttl_map:
                    del self.ttl_map[oldest_key]
                self.stats["evictions"] += 1
            
            # 새 값 추가
            self.cache[key] = value
            
            # TTL 설정
            ttl = ttl or self.default_ttl
            if ttl > 0:
                self.ttl_map[key] = time.time() + ttl
            
            self.stats["sets"] += 1
            return True
    
    async def delete(self, key: str) -> bool:
        """값 삭제"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                if key in self.ttl_map:
                    del self.ttl_map[key]
                self.stats["deletes"] += 1
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """키 존재 여부"""
        with self.lock:
            # TTL 체크
            if key in self.ttl_map:
                if time.time() > self.ttl_map[key]:
                    return False
            return key in self.cache
    
    async def clear(self) -> bool:
        """전체 캐시 초기화"""
        with self.lock:
            self.cache.clear()
            self.ttl_map.clear()
            return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        with self.lock:
            return {
                **self.stats,
                "size": len(self.cache),
                "max_size": self.max_size,
                "hit_rate": self.stats["hits"] / 
                           (self.stats["hits"] + self.stats["misses"])
                           if (self.stats["hits"] + self.stats["misses"]) > 0 else 0
            }
    
    async def cleanup_expired(self):
        """만료된 항목 정리"""
        with self.lock:
            now = time.time()
            expired_keys = [
                key for key, expire_time in self.ttl_map.items()
                if expire_time <= now
            ]
            
            for key in expired_keys:
                if key in self.cache:
                    del self.cache[key]
                del self.ttl_map[key]
            
            return len(expired_keys)


# 글로벌 캐시 인스턴스
_cache_instance: Optional[CacheManager] = None


def init_cache(
    cache_type: str = "redis",
    **kwargs
) -> CacheManager:
    """
    캐시 초기화
    
    Args:
        cache_type: 캐시 타입 (redis/memory)
        **kwargs: 추가 설정
    
    Returns:
        CacheManager 인스턴스
    """
    global _cache_instance
    
    if _cache_instance is None:
        if cache_type == "redis" and REDIS_AVAILABLE:
            try:
                _cache_instance = RedisCache(**kwargs)
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis cache: {e}")
                logger.info("Falling back to memory cache")
                _cache_instance = MemoryCache(**kwargs)
        else:
            _cache_instance = MemoryCache(**kwargs)
            logger.info("Memory cache initialized")
    
    return _cache_instance


def get_cache() -> Optional[CacheManager]:
    """캐시 인스턴스 반환"""
    return _cache_instance


async def close_cache():
    """캐시 종료"""
    global _cache_instance
    
    if _cache_instance:
        if hasattr(_cache_instance, 'close'):
            await _cache_instance.close()
        _cache_instance = None
        logger.info("Cache closed")
