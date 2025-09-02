"""
Routers package - Contains API endpoint routers
"""

from .chat_router import router as chat_router
from .health_router import router as health_router
from .auth_router import router as auth_router

__all__ = ["chat_router", "health_router", "auth_router"]
