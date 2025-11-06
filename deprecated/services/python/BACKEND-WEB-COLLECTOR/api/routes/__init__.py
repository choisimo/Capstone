"""
API 라우트 모듈
"""
from .crawler import router as crawler_router
from .analysis import router as analysis_router
from .monitoring import router as monitoring_router
from .workflow import router as workflow_router
from .system import router as system_router

__all__ = [
    'crawler_router',
    'analysis_router',
    'monitoring_router',
    'workflow_router',
    'system_router',
]
