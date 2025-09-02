"""
Main FastAPI application - Refactored with proper architecture
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import sys
import os

# 프로젝트 루트를 Python path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config import settings
from app.utils import initialize_application
from app.routers import chat_router, health_router, auth_router
from app.repositories import ChatStorage, SessionStorage

# Create FastAPI app
app = FastAPI(title=settings.APP_TITLE, version=settings.APP_VERSION)

# CORS 설정 (개발 환경에서는 모든 origin 허용)
all_allowed_origins = settings.ALLOWED_ORIGINS + settings.SSO_ALLOWED_ORIGINS
# 개발 환경에서는 모든 origin 허용
if os.getenv("ENVIRONMENT") != "production":
    all_allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=all_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize global storage (in production, this would be dependency injected)
chat_storage = ChatStorage()
session_storage = SessionStorage()

# Set dependencies for routers
from app.routers.chat_router import set_dependencies
from app.routers.auth_router import set_auth_dependencies
set_dependencies(chat_storage)
set_auth_dependencies(session_storage)

# Include routers
app.include_router(chat_router, tags=["chat"])
app.include_router(health_router, tags=["health"])
app.include_router(auth_router, tags=["authentication"])

# Static files mounting
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# Initialize application on startup
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    initialize_application(chat_storage)

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
