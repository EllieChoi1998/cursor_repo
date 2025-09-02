"""
Application utility functions
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List

from app.config import settings
from app.repositories import ChatStorage


def setup_static_files():
    """정적 파일 디렉토리 및 예시 파일 설정"""
    static_dir = settings.STATIC_DIR
    
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        
    docs_dir = settings.DOCS_DIR
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)
        
        # 예시 파일 생성
        for filename, content in settings.STATIC_EXAMPLES.items():
            filepath = os.path.join(docs_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)


def initialize_default_chatrooms(chat_storage: ChatStorage):
    """기본 채팅방들을 생성합니다."""
    print(f"🔍 Initializing default chatrooms. Current chatrooms: {len(chat_storage.chatrooms)}")
    
    # 시스템용 기본 채팅방은 생성하지 않음 (유저별 채팅방으로 변경)
    # 실제 사용자가 로그인할 때 채팅방이 생성되도록 함
    print("✅ User-specific chatrooms will be created upon login")


def initialize_application(chat_storage: ChatStorage):
    """애플리케이션 초기화"""
    print("🚀 애플리케이션 초기화 시작...")
    
    # 정적 파일 설정
    setup_static_files()
    
    # 기본 채팅방 생성
    initialize_default_chatrooms(chat_storage)
    
    print("✅ 애플리케이션 초기화 완료")


def get_app_info() -> Dict[str, Any]:
    """애플리케이션 정보 반환"""
    return {
        "message": settings.APP_TITLE,
        "version": settings.APP_VERSION,
        "endpoints": {
            "chat": "/chat (POST)",
            "docs": "/docs"
        }
    }
