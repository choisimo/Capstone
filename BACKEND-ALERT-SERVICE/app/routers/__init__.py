from .alerts import router as alerts_router
from .rules import router as rules_router
from .notifications import router as notifications_router

__all__ = ["alerts_router", "rules_router", "notifications_router"]