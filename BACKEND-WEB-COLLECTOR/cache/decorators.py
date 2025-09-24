"""
캐시 데코레이터
함수 결과 캐싱을 위한 데코레이터
"""
import functools
import hashlib
import json
import logging
from typing import Any, Callable, Optional, Union
import asyncio
import inspect

from .cache_manager import get_cache, init_cache

logger = logging.getLogger(__name__)


def cache_key_builder(
    prefix: str,
    *args,
    **kwargs
) -> str:
    """
    캐시 키 생성
    
    Args:
        prefix: 키 접두사
        *args: 위치 인자
        **kwargs: 키워드 인자
    
    Returns:
        캐시 키
    """
    key_parts = [prefix]
    
    # 위치 인자 처리
    for arg in args:
        if arg is None:
            key_parts.append("None")
        elif isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        elif isinstance(arg, (list, tuple)):
            key_parts.append(hashlib.md5(
                json.dumps(arg, sort_keys=True).encode()
            ).hexdigest()[:8])
        elif isinstance(arg, dict):
            key_parts.append(hashlib.md5(
                json.dumps(arg, sort_keys=True).encode()
            ).hexdigest()[:8])
        else:
            # 객체는 repr 해시
            key_parts.append(hashlib.md5(
                repr(arg).encode()
            ).hexdigest()[:8])
    
    # 키워드 인자 처리
    for k, v in sorted(kwargs.items()):
        if v is None:
            key_parts.append(f"{k}=None")
        elif isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}={v}")
        else:
            key_parts.append(f"{k}={hashlib.md5(str(v).encode()).hexdigest()[:8]}")
    
    return ":".join(key_parts)


def cache_result(
    ttl: int = 3600,
    prefix: Optional[str] = None,
    key_builder: Optional[Callable] = None,
    cache_none: bool = False,
    cache_errors: bool = False
):
    """
    함수 결과 캐싱 데코레이터
    
    Args:
        ttl: Time To Live (초)
        prefix: 캐시 키 접두사
        key_builder: 커스텀 키 빌더 함수
        cache_none: None 값 캐싱 여부
        cache_errors: 에러 캐싱 여부
    
    사용 예:
        @cache_result(ttl=600, prefix="user")
        async def get_user(user_id: int):
            return await db.get_user(user_id)
    """
    def decorator(func: Callable) -> Callable:
        # 함수명을 기본 접두사로 사용
        cache_prefix = prefix or f"{func.__module__}.{func.__name__}"
        
        # 비동기 함수 처리
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # 캐시 인스턴스 가져오기
                cache = get_cache()
                if not cache:
                    # 캐시 없으면 원본 함수 실행
                    return await func(*args, **kwargs)
                
                # 캐시 키 생성
                if key_builder:
                    cache_key = key_builder(cache_prefix, *args, **kwargs)
                else:
                    # self 제외 (메서드인 경우)
                    if args and hasattr(args[0], '__class__'):
                        cache_args = args[1:]
                    else:
                        cache_args = args
                    cache_key = cache_key_builder(cache_prefix, *cache_args, **kwargs)
                
                # 캐시 조회
                try:
                    cached_value = await cache.get(cache_key)
                    if cached_value is not None:
                        logger.debug(f"Cache hit for key: {cache_key}")
                        return cached_value
                    elif cached_value is None and not cache_none:
                        logger.debug(f"Cache miss for key: {cache_key}")
                except Exception as e:
                    logger.warning(f"Cache get error: {e}")
                
                # 원본 함수 실행
                try:
                    result = await func(*args, **kwargs)
                    
                    # 결과 캐싱
                    if result is not None or cache_none:
                        try:
                            await cache.set(cache_key, result, ttl)
                            logger.debug(f"Cached result for key: {cache_key}")
                        except Exception as e:
                            logger.warning(f"Cache set error: {e}")
                    
                    return result
                    
                except Exception as e:
                    if cache_errors:
                        # 에러도 캐싱 (짧은 TTL)
                        error_data = {"error": str(e), "type": type(e).__name__}
                        try:
                            await cache.set(cache_key, error_data, min(ttl, 60))
                        except:
                            pass
                    raise
            
            return async_wrapper
        
        # 동기 함수 처리
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # 동기 함수는 비동기로 변환하여 처리
                async def run():
                    cache = get_cache()
                    if not cache:
                        return func(*args, **kwargs)
                    
                    # 캐시 키 생성
                    if key_builder:
                        cache_key = key_builder(cache_prefix, *args, **kwargs)
                    else:
                        if args and hasattr(args[0], '__class__'):
                            cache_args = args[1:]
                        else:
                            cache_args = args
                        cache_key = cache_key_builder(cache_prefix, *cache_args, **kwargs)
                    
                    # 캐시 조회
                    try:
                        cached_value = await cache.get(cache_key)
                        if cached_value is not None:
                            return cached_value
                    except:
                        pass
                    
                    # 원본 함수 실행
                    result = func(*args, **kwargs)
                    
                    # 결과 캐싱
                    if result is not None or cache_none:
                        try:
                            await cache.set(cache_key, result, ttl)
                        except:
                            pass
                    
                    return result
                
                # 이벤트 루프에서 실행
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                return loop.run_until_complete(run())
            
            return sync_wrapper
    
    return decorator


def invalidate_cache(
    prefix: Optional[str] = None,
    key_builder: Optional[Callable] = None
):
    """
    캐시 무효화 데코레이터
    
    함수 실행 후 관련 캐시를 무효화
    
    Args:
        prefix: 캐시 키 접두사
        key_builder: 커스텀 키 빌더 함수
    
    사용 예:
        @invalidate_cache(prefix="user")
        async def update_user(user_id: int, data: dict):
            return await db.update_user(user_id, data)
    """
    def decorator(func: Callable) -> Callable:
        cache_prefix = prefix or f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # 원본 함수 실행
                result = await func(*args, **kwargs)
                
                # 캐시 무효화
                cache = get_cache()
                if cache:
                    if key_builder:
                        cache_key = key_builder(cache_prefix, *args, **kwargs)
                    else:
                        if args and hasattr(args[0], '__class__'):
                            cache_args = args[1:]
                        else:
                            cache_args = args
                        cache_key = cache_key_builder(cache_prefix, *cache_args, **kwargs)
                    
                    try:
                        await cache.delete(cache_key)
                        logger.debug(f"Invalidated cache for key: {cache_key}")
                    except Exception as e:
                        logger.warning(f"Cache invalidation error: {e}")
                
                return result
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # 원본 함수 실행
                result = func(*args, **kwargs)
                
                # 캐시 무효화
                async def invalidate():
                    cache = get_cache()
                    if cache:
                        if key_builder:
                            cache_key = key_builder(cache_prefix, *args, **kwargs)
                        else:
                            if args and hasattr(args[0], '__class__'):
                                cache_args = args[1:]
                            else:
                                cache_args = args
                            cache_key = cache_key_builder(cache_prefix, *cache_args, **kwargs)
                        
                        try:
                            await cache.delete(cache_key)
                        except:
                            pass
                
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                loop.run_until_complete(invalidate())
                
                return result
            
            return sync_wrapper
    
    return decorator


class CachedProperty:
    """
    캐시된 프로퍼티 디스크립터
    
    프로퍼티 값을 캐싱하여 재계산 방지
    
    사용 예:
        class MyClass:
            @CachedProperty
            def expensive_property(self):
                return expensive_calculation()
    """
    
    def __init__(self, func):
        self.func = func
        self.__doc__ = func.__doc__
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        
        # 캐시된 값 확인
        cache_attr = f"_cached_{self.func.__name__}"
        if hasattr(obj, cache_attr):
            return getattr(obj, cache_attr)
        
        # 계산 및 캐싱
        value = self.func(obj)
        setattr(obj, cache_attr, value)
        return value
    
    def __delete__(self, obj):
        # 캐시 무효화
        cache_attr = f"_cached_{self.func.__name__}"
        if hasattr(obj, cache_attr):
            delattr(obj, cache_attr)
