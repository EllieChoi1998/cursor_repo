from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import asyncio
import random
from datetime import datetime
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
import uuid

app = FastAPI(title="Data Analysis Chat API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 채팅방 모델
class ChatRoom(BaseModel):
    id: str
    created_at: datetime
    data_type: str  # 'pcm', 'cp', 'rag'

# 메시지 모델
class Message(BaseModel):
    id: str
    chatroom_id: str
    content: str
    message_type: str  # 'user', 'bot'
    timestamp: datetime
    data_type: str  # 'pcm', 'cp', 'rag'

# 응답 모델
class BotResponse(BaseModel):
    id: str
    message_id: str  # 연결된 사용자 메시지 ID
    chatroom_id: str
    content: Dict[str, Any]
    timestamp: datetime

# 요청 모델
class ChatRequest(BaseModel):
    choice: str  # 'pcm', 'cp', 'rag'
    message: str
    chatroom_id: str  # 필수 필드로 변경

# 채팅방 생성 요청 모델
class CreateChatRoomRequest(BaseModel):
    data_type: str  # 'pcm', 'cp', 'rag'

# 채팅방 목록 응답 모델
class ChatRoomListResponse(BaseModel):
    chatrooms: List[ChatRoom]

# 채팅방 상세 응답 모델
class ChatRoomDetailResponse(BaseModel):
    chatroom: ChatRoom
    messages: List[Message]
    responses: List[BotResponse]

# 메모리 기반 저장소 (나중에 SQL로 교체 가능)
class ChatStorage:
    def __init__(self):
        self.chatrooms: Dict[str, ChatRoom] = {}
        self.messages: Dict[str, Message] = {}
        self.responses: Dict[str, BotResponse] = {}
    
    def create_chatroom(self, data_type: str) -> ChatRoom:
        """새 채팅방 생성"""
        chatroom_id = str(uuid.uuid4())
        chatroom = ChatRoom(
            id=chatroom_id,
            created_at=datetime.now(),
            data_type=data_type
        )
        self.chatrooms[chatroom_id] = chatroom
        return chatroom
    
    def get_chatroom(self, chatroom_id: str) -> Optional[ChatRoom]:
        """채팅방 조회"""
        return self.chatrooms.get(chatroom_id)
    
    def get_all_chatrooms(self) -> List[ChatRoom]:
        """모든 채팅방 조회"""
        return list(self.chatrooms.values())
    
    def delete_chatroom(self, chatroom_id: str) -> bool:
        """채팅방 삭제"""
        if chatroom_id in self.chatrooms:
            del self.chatrooms[chatroom_id]
            # 관련 메시지와 응답도 삭제
            self.messages = {k: v for k, v in self.messages.items() if v.chatroom_id != chatroom_id}
            self.responses = {k: v for k, v in self.responses.items() if v.chatroom_id != chatroom_id}
            return True
        return False
    
    def add_message(self, chatroom_id: str, content: str, message_type: str, data_type: str) -> Message:
        """메시지 추가"""
        message_id = str(uuid.uuid4())
        message = Message(
            id=message_id,
            chatroom_id=chatroom_id,
            content=content,
            message_type=message_type,
            timestamp=datetime.now(),
            data_type=data_type
        )
        self.messages[message_id] = message
        return message
    
    def get_messages_by_chatroom(self, chatroom_id: str) -> List[Message]:
        """채팅방의 메시지 조회"""
        return [msg for msg in self.messages.values() if msg.chatroom_id == chatroom_id]
    
    def add_response(self, message_id: str, chatroom_id: str, content: Dict[str, Any]) -> BotResponse:
        """봇 응답 추가"""
        response_id = str(uuid.uuid4())
        response = BotResponse(
            id=response_id,
            message_id=message_id,
            chatroom_id=chatroom_id,
            content=content,
            timestamp=datetime.now()
        )
        self.responses[response_id] = response
        return response
    
    def get_responses_by_chatroom(self, chatroom_id: str) -> List[BotResponse]:
        """채팅방의 응답 조회"""
        return [resp for resp in self.responses.values() if resp.chatroom_id == chatroom_id]

# 전역 저장소 인스턴스
chat_storage = ChatStorage()

# 기본 채팅방 생성
def initialize_default_chatrooms():
    """기본 채팅방들을 생성합니다."""
    if not chat_storage.get_all_chatrooms():
        # 일반 채팅방 (기본) - choice는 pcm로 유지하되 메시지는 일반적인 내용
        general_room = chat_storage.create_chatroom('pcm')
        chat_storage.add_message(general_room.id, '안녕하세요! 데이터 분석 채팅 어시스턴트입니다. PCM, CP, RAG 분석에 대해 질문해주세요.', 'bot', 'pcm')

# 앱 시작 시 기본 채팅방 생성
initialize_default_chatrooms()

# 데이터 타입별 지원되는 명령어
SUPPORTED_COMMANDS = {
    'pcm': {
        'trend': ['trend', '트렌드', '차트', '그래프', '분석'],
        'commonality': ['commonality', '커먼', '공통', '분석']
    },
    'cp': {
        'analysis': ['analysis', '분석', '성능', '모니터링'],
        'performance': ['performance', '성능', '측정', '평가']
    },
    'rag': {
        'search': ['search', '검색', '찾기', '조회'],
        'summary': ['summary', '요약', '정리', '개요']
    }
}

def is_valid_command(choice: str, message: str) -> tuple[bool, str, str]:
    """
    메시지가 유효한 명령어인지 검사
    Returns: (is_valid, command_type, error_message)
    """
    message_lower = message.lower().strip()
    
    # 데이터 타입이 지원되지 않는 경우
    if choice not in SUPPORTED_COMMANDS:
        return False, "", f"지원되지 않는 데이터 타입: {choice}"
    
    # 빈 메시지 체크
    if not message_lower:
        return False, "", "메시지를 입력해주세요."
    
    # 지원되는 명령어 체크
    for command_type, keywords in SUPPORTED_COMMANDS[choice].items():
        for keyword in keywords:
            if keyword in message_lower:
                return True, command_type, ""
    
    # 유효하지 않은 메시지
    return False, "", f"'{choice.upper()}' 데이터 타입에서 지원되지 않는 명령어입니다. 사용 가능한 명령어: {list(SUPPORTED_COMMANDS[choice].keys())}"

def generate_pcm_trend_data() -> list:
    """PCM 트렌드 데이터 생성"""
    data = []
    for i in range(1, 21):
        data.append({
            'DATE_WAFER_ID': i,
            'MIN': round(random.uniform(8, 12), 2),
            'MAX': round(random.uniform(18, 22), 2),
            'Q1': round(random.uniform(14, 16), 2),
            'Q2': round(random.uniform(15, 17), 2),
            'Q3': round(random.uniform(16, 18), 2),
            'DEVICE': random.choice(['A', 'B', 'C']),
            'USL': 30,
            'TGT': 15,
            'LSL': 1,
            'UCL': 25,
            'LCL': 6
        })
    return data

def generate_commonality_data() -> tuple[list, dict]:
    """Commonality 데이터 생성"""
    # 기본 PCM 데이터
    data = generate_pcm_trend_data()
    
    # Commonality 정보
    commonality = {
        'good_lots': ['LOT001', 'LOT002', 'LOT003'],
        'bad_lots': ['LOT004', 'LOT005'],
        'good_wafers': ['WAFER001', 'WAFER002', 'WAFER003'],
        'bad_wafers': ['WAFER004', 'WAFER005']
    }
    
    return data, commonality

def generate_cp_analysis_data() -> list:
    """CP 분석 데이터 생성"""
    data = []
    for i in range(1, 16):
        data.append({
            'timestamp': f'2024-01-{i:02d}',
            'critical_path_length': round(random.uniform(10, 20), 2),
            'performance_score': round(random.uniform(0.7, 0.95), 3),
            'bottleneck_count': random.randint(1, 5),
            'optimization_potential': round(random.uniform(0.1, 0.3), 3)
        })
    return data

def generate_rag_search_data() -> dict:
    """RAG 검색 데이터 생성"""
    return {
        'query': 'PCM 데이터 분석',
        'results': [
            {'title': 'PCM 트렌드 분석 가이드', 'relevance': 0.95, 'content': 'PCM 데이터의 트렌드 분석 방법...'},
            {'title': 'Commonality 분석 기법', 'relevance': 0.88, 'content': 'Commonality 분석을 통한 품질 관리...'},
            {'title': '데이터 시각화 모범 사례', 'relevance': 0.82, 'content': '효과적인 데이터 시각화 방법...'}
        ],
        'total_results': 15,
        'search_time': 0.23
    }

async def process_chat_request(choice: str, message: str, chatroom_id: str):
    """채팅 요청 처리"""
    # 채팅방 확인
    chatroom = chat_storage.get_chatroom(chatroom_id)
    if not chatroom:
        yield f"data: {json.dumps({'msg': '존재하지 않는 채팅방입니다.'})}\n\n"
        return
    
    # 유효성 검사
    is_valid, command_type, error_msg = is_valid_command(choice, message)
    
    if not is_valid:
        # 실패한 메시지는 저장하지 않고 에러만 반환
        yield f"data: {json.dumps({'msg': error_msg})}\n\n"
        return
    
    # 유효한 메시지만 저장
    user_message = chat_storage.add_message(chatroom_id, message, 'user', choice)
    
    # 처리 중 메시지 (저장하지 않고 프론트엔드에서만 표시)
    yield f"data: {json.dumps({'status': 'processing'})}\n\n"
    await asyncio.sleep(0.5)
    
    # 데이터 타입별 처리
    if choice == 'pcm':
        if command_type == 'trend':
            data = generate_pcm_trend_data()
            response = {
                'result': 'lot_start',
                'real_data': data,
                'sql': 'SELECT * FROM pcm_data WHERE date >= "2024-01-01" ORDER BY date_wafer_id',
                'timestamp': datetime.now().isoformat()
            }
        elif command_type == 'commonality':
            data, commonality = generate_commonality_data()
            response = {
                'result': 'commonality_start',
                'real_data': data,
                'determined': commonality,
                'SQL': 'SELECT * FROM pcm_data WHERE lot_type IN ("good", "bad")',
                'timestamp': datetime.now().isoformat()
            }
    
    elif choice == 'cp':
        if command_type == 'analysis':
            data = generate_cp_analysis_data()
            response = {
                'result': 'cp_analysis',
                'real_data': data,
                'sql': 'SELECT * FROM cp_data WHERE analysis_date >= "2024-01-01"',
                'timestamp': datetime.now().isoformat()
            }
        elif command_type == 'performance':
            data = generate_cp_analysis_data()
            response = {
                'result': 'cp_performance',
                'real_data': data,
                'sql': 'SELECT * FROM cp_performance WHERE date >= "2024-01-01"',
                'timestamp': datetime.now().isoformat()
            }
    
    elif choice == 'rag':
        if command_type == 'search':
            data = generate_rag_search_data()
            response = {
                'result': 'rag_search',
                'real_data': data,
                'query': message,
                'timestamp': datetime.now().isoformat()
            }
        elif command_type == 'summary':
            data = generate_rag_search_data()
            response = {
                'result': 'rag_summary',
                'real_data': data,
                'summary': 'PCM 데이터 분석에 대한 종합적인 요약 정보입니다.',
                'timestamp': datetime.now().isoformat()
            }
    
    # 성공한 경우에만 저장
    bot_response = chat_storage.add_response(user_message.id, chatroom_id, response)
    
    # 성공 메시지 저장
    success_message = f"✅ {choice.upper()} 데이터를 성공적으로 처리했습니다!"
    chat_storage.add_message(chatroom_id, success_message, 'bot', choice)
    
    # 최종 응답
    chat_response = {
        'chat_id': chatroom_id,
        'message_id': user_message.id,
        'response_id': bot_response.id,
        'response': response
    }
    
    yield f"data: {json.dumps(chat_response)}\n\n"

@app.post("/api/chatrooms")
async def create_chatroom(request: CreateChatRoomRequest):
    """새 채팅방 생성"""
    try:
        chatroom = chat_storage.create_chatroom(request.data_type)
        return chatroom  # 직접 chatroom 객체 반환
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅방 생성 실패: {str(e)}")

@app.get("/api/chatrooms")
async def get_chatrooms():
    """모든 채팅방 조회"""
    try:
        chatrooms = chat_storage.get_all_chatrooms()
        return {"success": True, "chatrooms": chatrooms}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅방 조회 실패: {str(e)}")

@app.get("/api/chatrooms/{chatroom_id}")
async def get_chatroom_detail(chatroom_id: str):
    """채팅방 상세 정보 조회"""
    try:
        chatroom = chat_storage.get_chatroom(chatroom_id)
        if not chatroom:
            raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
        
        messages = chat_storage.get_messages_by_chatroom(chatroom_id)
        responses = chat_storage.get_responses_by_chatroom(chatroom_id)
        
        return {
            "success": True,
            "chatroom": chatroom,
            "messages": messages,
            "responses": responses
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅방 상세 조회 실패: {str(e)}")

@app.delete("/api/chatrooms/{chatroom_id}")
async def delete_chatroom(chatroom_id: str):
    """채팅방 삭제"""
    try:
        success = chat_storage.delete_chatroom(chatroom_id)
        if not success:
            raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
        
        return {"success": True, "message": "채팅방이 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅방 삭제 실패: {str(e)}")

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """스트리밍 채팅 API 엔드포인트"""
    
    async def generate():
        try:
            async for chunk in process_chat_request(request.choice, request.message, request.chatroom_id):
                yield chunk
        except Exception as e:
            error_response = {"msg": f"서버 내부 오류: {str(e)}"}
            yield f"data: {json.dumps(error_response)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Data Analysis Chat API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/chat (POST)",
            "docs": "/docs"
        },
        "supported_data_types": list(SUPPORTED_COMMANDS.keys())
    }

@app.get("/api/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 