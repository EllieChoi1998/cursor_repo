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
    
    if not chat_storage.chatrooms:
        print("📝 Creating default chatroom...")
        # 일반 채팅방 (기본) - choice는 pcm로 유지하되 메시지는 일반적인 내용
        general_room = chat_storage.create_chatroom()
        print(f"✅ Created default chatroom with ID: {general_room.id}")
        
        chat_storage.add_message(
            general_room.id, 
            '안녕하세요! 데이터 분석 채팅 어시스턴트입니다. PCM, INLINE, RAG 분석에 대해 질문해주세요.', 
            'bot', 
            'pcm'
        )
        print(f"📝 Added welcome message to chatroom {general_room.id}")
        
        # 샘플 채팅 히스토리 추가 (시간 차이를 두어 실제 상황 시뮬레이션)
        sample_data = [{'DATE_WAFER_ID': '2025-06-18:36:57:54_A12345678998999', 'MIN': 10, 'MAX': 20, 'Q1': 15, 'Q2': 16, 'Q3': 17, 'DEVICE': 'A'}]
        user_time = datetime.now()
        response_time = user_time.replace(second=user_time.second + 2)  # 2초 후 응답
        
        chat_storage.add_chat_history(
            general_room.id, 
            "PCM 트렌드를 보여줘", 
            json.dumps({
                'result': 'lot_start',
                'real_data': sample_data,
                'sql': 'SELECT * FROM pcm_data WHERE date >= "2024-01-01" ORDER BY date_wafer_id',
                'timestamp': datetime.now().isoformat()
            }),
            user_time=user_time,
            response_time=response_time
        )
        print(f"📝 Added sample chat history to chatroom {general_room.id}")
    else:
        print(f"✅ Default chatrooms already exist: {list(chat_storage.chatrooms.keys())}")


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
