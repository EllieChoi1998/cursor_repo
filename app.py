from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
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
    id: int  # 정수로 변경
    created_at: datetime
    data_type: str  # 'pcm', 'cp', 'rag'

# 채팅 기록 모델 (새로 추가)
class ChatHistory(BaseModel):
    chat_id: int
    chatroom_id: int
    user_message: str
    chat_time: datetime
    bot_response: str
    response_time: datetime

# 메시지 모델
class Message(BaseModel):
    id: str
    chatroom_id: int  # 정수로 변경
    content: str
    message_type: str  # 'user', 'bot'
    timestamp: datetime
    data_type: str  # 'pcm', 'cp', 'rag'

# 응답 모델
class BotResponse(BaseModel):
    id: str
    message_id: str  # 연결된 사용자 메시지 ID
    chatroom_id: int  # 정수로 변경
    content: Dict[str, Any]
    timestamp: datetime

# 요청 모델
class ChatRequest(BaseModel):
    choice: str  # 'pcm', 'cp', 'rag'
    message: str
    chatroom_id: int  # 정수로 변경

# 채팅방 생성 요청 모델
class CreateChatRoomRequest(BaseModel):
    data_type: str  # 'pcm', 'cp', 'rag'

# 채팅방 목록 응답 모델 (API 명세에 맞게 수정)
class ChatRoomListItem(BaseModel):
    id: int
    message_count: int
    last_activity: datetime

class ChatRoomListResponse(BaseModel):
    chatrooms: List[ChatRoomListItem]

# 채팅방 히스토리 응답 모델 (새로 추가)
class ChatHistoryResponse(BaseModel):
    chatroom_id: int
    recent_conversations: List[ChatHistory]
    count: int

# 채팅방 상세 응답 모델
class ChatRoomDetailResponse(BaseModel):
    chatroom: ChatRoom
    messages: List[Message]
    responses: List[BotResponse]

# 메모리 기반 저장소 (나중에 SQL로 교체 가능)
class ChatStorage:
    def __init__(self):
        self.chatrooms: Dict[int, ChatRoom] = {}
        self.messages: Dict[str, Message] = {}
        self.responses: Dict[str, BotResponse] = {}
        self.chat_histories: Dict[int, List[ChatHistory]] = {}  # 채팅 기록 저장
        self.next_chatroom_id = 1
        self.next_chat_id = 1
    
    def create_chatroom(self, data_type: str) -> ChatRoom:
        """새 채팅방 생성"""
        chatroom_id = self.next_chatroom_id
        self.next_chatroom_id += 1
        
        chatroom = ChatRoom(
            id=chatroom_id,
            created_at=datetime.now(),
            data_type=data_type
        )
        self.chatrooms[chatroom_id] = chatroom
        self.chat_histories[chatroom_id] = []  # 빈 히스토리 초기화
        return chatroom
    
    def get_chatroom(self, chatroom_id: int) -> Optional[ChatRoom]:
        """채팅방 조회"""
        return self.chatrooms.get(chatroom_id)
    
    def get_all_chatrooms(self) -> List[ChatRoomListItem]:
        """모든 채팅방 조회 (API 명세 형식으로)"""
        result = []
        for chatroom_id, chatroom in self.chatrooms.items():
            message_count = len(self.chat_histories.get(chatroom_id, []))
            last_activity = chatroom.created_at
            
            # 가장 최근 활동 시간 찾기
            histories = self.chat_histories.get(chatroom_id, [])
            if histories:
                last_activity = max(history.response_time for history in histories)
            
            result.append(ChatRoomListItem(
                id=chatroom_id,
                message_count=message_count,
                last_activity=last_activity
            ))
        
        # 최근 활동 순으로 정렬
        result.sort(key=lambda x: x.last_activity, reverse=True)
        return result
    
    def get_chatroom_history(self, chatroom_id: int) -> Optional[ChatHistoryResponse]:
        """채팅방 히스토리 조회"""
        if chatroom_id not in self.chatrooms:
            return None
        
        histories = self.chat_histories.get(chatroom_id, [])
        return ChatHistoryResponse(
            chatroom_id=chatroom_id,
            recent_conversations=histories,
            count=len(histories)
        )
    
    def delete_chatroom(self, chatroom_id: int) -> bool:
        """채팅방 삭제"""
        if chatroom_id in self.chatrooms:
            del self.chatrooms[chatroom_id]
            # 관련 메시지와 응답, 히스토리도 삭제
            self.messages = {k: v for k, v in self.messages.items() if v.chatroom_id != chatroom_id}
            self.responses = {k: v for k, v in self.responses.items() if v.chatroom_id != chatroom_id}
            if chatroom_id in self.chat_histories:
                del self.chat_histories[chatroom_id]
            return True
        return False
    
    def add_message(self, chatroom_id: int, content: str, message_type: str, data_type: str) -> Message:
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
    
    def add_chat_history(self, chatroom_id: int, user_message: str, bot_response: str) -> ChatHistory:
        """채팅 히스토리 추가"""
        chat_id = self.next_chat_id
        self.next_chat_id += 1
        
        now = datetime.now()
        history = ChatHistory(
            chat_id=chat_id,
            chatroom_id=chatroom_id,
            user_message=user_message,
            chat_time=now,
            bot_response=bot_response,
            response_time=now
        )
        
        if chatroom_id not in self.chat_histories:
            self.chat_histories[chatroom_id] = []
        
        self.chat_histories[chatroom_id].append(history)
        return history
    
    def get_messages_by_chatroom(self, chatroom_id: int) -> List[Message]:
        """채팅방의 메시지 조회"""
        return [msg for msg in self.messages.values() if msg.chatroom_id == chatroom_id]
    
    def add_response(self, message_id: str, chatroom_id: int, content: Dict[str, Any]) -> BotResponse:
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
    
    def get_responses_by_chatroom(self, chatroom_id: int) -> List[BotResponse]:
        """채팅방의 응답 조회"""
        return [resp for resp in self.responses.values() if resp.chatroom_id == chatroom_id]

# 전역 저장소 인스턴스
chat_storage = ChatStorage()

# 기본 채팅방 생성
def initialize_default_chatrooms():
    """기본 채팅방들을 생성합니다."""
    if not chat_storage.chatrooms:
        # 일반 채팅방 (기본) - choice는 pcm로 유지하되 메시지는 일반적인 내용
        general_room = chat_storage.create_chatroom('pcm')
        chat_storage.add_message(general_room.id, '안녕하세요! 데이터 분석 채팅 어시스턴트입니다. PCM, CP, RAG 분석에 대해 질문해주세요.', 'bot', 'pcm')
        
        # 샘플 채팅 히스토리 추가
        sample_data = [{'DATE_WAFER_ID': 1, 'MIN': 10, 'MAX': 20, 'Q1': 15, 'Q2': 16, 'Q3': 17, 'DEVICE': 'A'}]
        chat_storage.add_chat_history(
            general_room.id, 
            "PCM 트렌드를 보여줘", 
            json.dumps({
                'result': 'lot_start',
                'real_data': sample_data,
                'sql': 'SELECT * FROM pcm_data WHERE date >= "2024-01-01" ORDER BY date_wafer_id',
                'timestamp': datetime.now().isoformat()
            })
        )

# 앱 시작 시 기본 채팅방 생성
initialize_default_chatrooms()

# 데이터 타입별 지원되는 명령어
SUPPORTED_COMMANDS = {
    'pcm': {
        'trend': ['trend', '트렌드', '차트', '그래프', '분석'],
        'commonality': ['commonality', '커먼', '공통', '분석'],
        'point': ['point', '포인트', 'site', '사이트']
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

def generate_pcm_point_data() -> list:
    """PCM 트렌드 포인트(라인+마커)용 예시 데이터 (고정값)"""
    return [
        {'DATE_WAFER_ID': 1, 'PCM_SITE': '1', 'VALUE': 10},
        {'DATE_WAFER_ID': 1, 'PCM_SITE': '2', 'VALUE': 11},
        {'DATE_WAFER_ID': 1, 'PCM_SITE': '3', 'VALUE': 12},
        {'DATE_WAFER_ID': 1, 'PCM_SITE': '4', 'VALUE': 13},
        {'DATE_WAFER_ID': 1, 'PCM_SITE': '5', 'VALUE': 14},
        {'DATE_WAFER_ID': 2, 'PCM_SITE': '1', 'VALUE': 11},
        {'DATE_WAFER_ID': 2, 'PCM_SITE': '2', 'VALUE': 12},
        {'DATE_WAFER_ID': 2, 'PCM_SITE': '3', 'VALUE': 13},
        {'DATE_WAFER_ID': 2, 'PCM_SITE': '4', 'VALUE': 14},
        {'DATE_WAFER_ID': 2, 'PCM_SITE': '5', 'VALUE': 15},
        {'DATE_WAFER_ID': 3, 'PCM_SITE': '1', 'VALUE': 10},
        {'DATE_WAFER_ID': 3, 'PCM_SITE': '2', 'VALUE': 11},
        {'DATE_WAFER_ID': 3, 'PCM_SITE': '3', 'VALUE': 12},
        {'DATE_WAFER_ID': 3, 'PCM_SITE': '4', 'VALUE': 13},
        {'DATE_WAFER_ID': 3, 'PCM_SITE': '5', 'VALUE': 14},
        {'DATE_WAFER_ID': 4, 'PCM_SITE': '1', 'VALUE': 12},
        {'DATE_WAFER_ID': 4, 'PCM_SITE': '2', 'VALUE': 13},
        {'DATE_WAFER_ID': 4, 'PCM_SITE': '3', 'VALUE': 14},
        {'DATE_WAFER_ID': 4, 'PCM_SITE': '4', 'VALUE': 15},
        {'DATE_WAFER_ID': 4, 'PCM_SITE': '5', 'VALUE': 16},
        {'DATE_WAFER_ID': 5, 'PCM_SITE': '1', 'VALUE': 14},
        {'DATE_WAFER_ID': 5, 'PCM_SITE': '2', 'VALUE': 13},
        {'DATE_WAFER_ID': 5, 'PCM_SITE': '3', 'VALUE': 13},
        {'DATE_WAFER_ID': 5, 'PCM_SITE': '4', 'VALUE': 12},
        {'DATE_WAFER_ID': 5, 'PCM_SITE': '5', 'VALUE': 11},
    ]

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

def generate_rag_answer_data() -> list:
    return [
        {
            "file_name": "example1.pdf",
            "file_path": "/static/docs/example1.pdf",
            "similarity": 0.98
        },
        {
            "file_name": "example2.pdf",
            "file_path": "/static/docs/example2.pdf",
            "similarity": 0.92
        },
        {
            "file_name": "example3.pdf",
            "file_path": "/static/docs/example3.pdf",
            "similarity": 0.89
        }
    ]

async def process_chat_request(choice: str, message: str, chatroom_id: int):
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
        elif command_type == 'point':
            data = generate_pcm_point_data()
            response = {
                'result': 'lot_point',
                'real_data': data,
                'sql': 'SELECT * FROM pcm_data WHERE type = "point"',
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
            answer = generate_rag_answer_data()
            response = {
                'result': 'rag_search',
                'answer': answer,
                'related_slides': [],
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
    
    # 채팅 히스토리에 추가
    chat_storage.add_chat_history(chatroom_id, message, json.dumps(response))
    
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

@app.get("/chatrooms")
async def get_chatrooms():
    """모든 채팅방 조회 (API 명세에 맞는 형식)"""
    try:
        chatrooms = chat_storage.get_all_chatrooms()
        return {"chatrooms": chatrooms}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅방 조회 실패: {str(e)}")

@app.get("/chatrooms/{chatroom_id}/history")
async def get_chatroom_history(chatroom_id: int):
    """채팅방 히스토리 조회 (API 명세에 맞는 형식)"""
    try:
        history = chat_storage.get_chatroom_history(chatroom_id)
        if not history:
            raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
        
        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅방 히스토리 조회 실패: {str(e)}")

@app.get("/api/chatrooms")
async def get_chatrooms_legacy():
    """모든 채팅방 조회 (기존 API 호환)"""
    try:
        chatrooms = chat_storage.get_all_chatrooms()
        return {"success": True, "chatrooms": chatrooms}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅방 조회 실패: {str(e)}")

@app.get("/api/chatrooms/{chatroom_id}")
async def get_chatroom_detail(chatroom_id: int):
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
async def delete_chatroom(chatroom_id: int):
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
    app.mount("/static", StaticFiles(directory="static"), name="static")
    uvicorn.run(app, host="0.0.0.0", port=8000) 