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

# 정적 파일 서빙 설정
import os
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
    # 예시 파일 생성
    docs_dir = os.path.join(static_dir, "docs")
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)
        # 예시 PDF 파일 생성 (실제로는 텍스트 파일로 대체)
        with open(os.path.join(docs_dir, "example1.pdf"), "w", encoding="utf-8") as f:
            f.write("PCM 데이터 분석 가이드\n\n이 문서는 PCM 데이터 분석 방법에 대한 상세한 가이드입니다.")
        with open(os.path.join(docs_dir, "example2.pdf"), "w", encoding="utf-8") as f:
            f.write("Commonality 분석 기법\n\nCommonality 분석을 통한 품질 관리 방법을 설명합니다.")
        with open(os.path.join(docs_dir, "example3.pdf"), "w", encoding="utf-8") as f:
            f.write("데이터 시각화 모범 사례\n\n효과적인 데이터 시각화 방법과 모범 사례를 제시합니다.")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 채팅방 모델
class ChatRoom(BaseModel):
    id: int  # 정수로 변경

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

# 메시지 수정 요청 모델 (새로 추가)
class EditMessageRequest(BaseModel):
    choice: str  # 'pcm', 'cp', 'rag'
    message: str
    chatroom_id: int
    original_chat_id: int  # 기존 chat_id

# 채팅방 생성 요청 모델 제거 (파라미터 없음)

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
    
    def create_chatroom(self) -> ChatRoom:
        """새 채팅방 생성 (파라미터 없음)"""
        chatroom_id = self.next_chatroom_id
        self.next_chatroom_id += 1
        
        chatroom = ChatRoom(
            id=chatroom_id
        )
        self.chatrooms[chatroom_id] = chatroom
        self.chat_histories[chatroom_id] = []  # 빈 히스토리 초기화
        return chatroom
    
    def get_chatroom(self, chatroom_id: int) -> Optional[ChatRoom]:
        """채팅방 조회"""
        return self.chatrooms.get(chatroom_id)
    
    def get_all_chatrooms(self) -> List[ChatRoomListItem]:
        """모든 채팅방 조회 (API 명세 형식으로)"""
        print(f"🔍 get_all_chatrooms called. Chatrooms: {list(self.chatrooms.keys())}")
        result = []
        for chatroom_id, chatroom in self.chatrooms.items():
            message_count = len(self.chat_histories.get(chatroom_id, []))
            
            # 가장 최근 활동 시간 찾기 (기본값은 현재 시간)
            last_activity = datetime.now()
            histories = self.chat_histories.get(chatroom_id, [])
            if histories:
                last_activity = max(history.response_time for history in histories)
            
            item = ChatRoomListItem(
                id=chatroom_id,
                message_count=message_count,
                last_activity=last_activity
            )
            result.append(item)
            print(f"📋 Added chatroom {chatroom_id}: {item}")
        
        # 최근 활동 순으로 정렬
        result.sort(key=lambda x: x.last_activity, reverse=True)
        print(f"✅ Returning {len(result)} chatrooms")
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
    
    def add_chat_history(self, chatroom_id: int, user_message: str, bot_response: str, user_time: datetime = None, response_time: datetime = None) -> ChatHistory:
        """채팅 히스토리 추가"""
        chat_id = self.next_chat_id
        self.next_chat_id += 1
        
        print(f"🔧 Creating chat history with chat_id: {chat_id} for chatroom: {chatroom_id}")
        
        # 시간 설정: 파라미터로 받은 시간이 있으면 사용, 없으면 현재 시간
        chat_time = user_time if user_time else datetime.now()
        bot_response_time = response_time if response_time else datetime.now()
        
        history = ChatHistory(
            chat_id=chat_id,
            chatroom_id=chatroom_id,
            user_message=user_message,
            chat_time=chat_time,
            bot_response=bot_response,
            response_time=bot_response_time
        )
        
        if chatroom_id not in self.chat_histories:
            self.chat_histories[chatroom_id] = []
        
        self.chat_histories[chatroom_id].append(history)
        print(f"✅ Added chat history with chat_id: {chat_id}")
        print(f"📅 Chat time: {chat_time}, Response time: {bot_response_time}")
        return history
    
    def edit_chat_history(self, chatroom_id: int, chat_id: int, user_message: str, bot_response: str) -> Optional[ChatHistory]:
        """채팅 히스토리 수정 (기존 chat_id 유지)"""
        if chatroom_id not in self.chat_histories:
            print(f"❌ Chatroom {chatroom_id} not found in histories")
            return None
        
        # 기존 히스토리에서 해당 chat_id를 찾아 업데이트
        for history in self.chat_histories[chatroom_id]:
            if history.chat_id == chat_id:
                print(f"🔧 Updating existing chat history with chat_id: {chat_id}")
                
                # 히스토리 내용 업데이트
                history.user_message = user_message
                history.chat_time = datetime.now()
                history.bot_response = bot_response
                history.response_time = datetime.now()
                
                print(f"✅ Updated chat history with chat_id: {chat_id}")
                print(f"📅 Updated time: {history.chat_time}")
                return history
        
        print(f"❌ Chat history with chat_id {chat_id} not found in chatroom {chatroom_id}")
        return None
    
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
    print(f"🔍 Initializing default chatrooms. Current chatrooms: {len(chat_storage.chatrooms)}")
    if not chat_storage.chatrooms:
        print("📝 Creating default chatroom...")
        # 일반 채팅방 (기본) - choice는 pcm로 유지하되 메시지는 일반적인 내용
        general_room = chat_storage.create_chatroom()
        print(f"✅ Created default chatroom with ID: {general_room.id}")
        
        chat_storage.add_message(general_room.id, '안녕하세요! 데이터 분석 채팅 어시스턴트입니다. PCM, CP, RAG 분석에 대해 질문해주세요.', 'bot', 'pcm')
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

def analyze_query(message: str) -> tuple[str, str, str]:
    """
    메시지를 분석하여 어떤 타입의 처리가 필요한지 결정
    Returns: (data_type, command_type, error_message)
    """
    message_lower = message.lower().strip()
    
    # 빈 메시지 체크
    if not message_lower:
        return "", "", "메시지를 입력해주세요."
    
    # RAG 관련 키워드 우선 검사
    rag_keywords = ['검색', 'search', '찾기', '조회', '문서', 'document', '파일', 'file', '설명', '요약', 'summary']
    for keyword in rag_keywords:
        if keyword in message_lower:
            return 'rag', 'search', ""
    
    # PCM 관련 키워드 검사
    pcm_keywords = ['pcm', 'trend', '트렌드', '차트', '그래프', 'commonality', '커먼', '공통', 'point', '포인트', 'site', '사이트']
    for keyword in pcm_keywords:
        if keyword in message_lower:
            if any(k in message_lower for k in ['trend', '트렌드', '차트', '그래프']):
                return 'pcm', 'trend', ""
            elif any(k in message_lower for k in ['commonality', '커먼', '공통']):
                return 'pcm', 'commonality', ""
            elif any(k in message_lower for k in ['point', '포인트', 'site', '사이트']):
                return 'pcm', 'point', ""
            else:
                return 'pcm', 'trend', ""  # 기본값
    
    # CP 관련 키워드 검사
    cp_keywords = ['cp', 'critical', 'path', '경로', 'analysis', '분석', 'performance', '성능', '모니터링']
    for keyword in cp_keywords:
        if keyword in message_lower:
            if any(k in message_lower for k in ['performance', '성능', '모니터링']):
                return 'cp', 'performance', ""
            else:
                return 'cp', 'analysis', ""
    
    # 기본적으로 RAG로 처리 (질문이나 일반적인 요청)
    return 'rag', 'general', ""

def generate_pcm_trend_data() -> list:
    """PCM 트렌드 데이터 생성"""
    data = []
    para_types = ['PARA1', 'PARA2', 'PARA3', 'PARA4', 'PARA5']  # PARA 타입들
    for i in range(1, 1000):
        data.append({
            'DATE_WAFER_ID': f'2025-06-{i}:36:57:54_A12345678998999',
            'MIN': round(random.uniform(8, 12), 2),
            'MAX': round(random.uniform(18, 22), 2),
            'Q1': round(random.uniform(14, 16), 2),
            'Q2': round(random.uniform(15, 17), 2),
            'Q3': round(random.uniform(16, 18), 2),
            'DEVICE': random.choice(['A', 'B', 'C']),
            'PARA': random.choice(para_types),  # PARA 컬럼 추가
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
        {'DATE_WAFER_ID': '2025-06-1:36:57:54_A12345678998999', 'PCM_SITE': '1', 'VALUE': 10},
        {'DATE_WAFER_ID': '2025-06-2:36:57:54_A12345678998999', 'PCM_SITE': '2', 'VALUE': 11},
        {'DATE_WAFER_ID': '2025-06-3:36:57:54_A12345678998999', 'PCM_SITE': '3', 'VALUE': 12},
        {'DATE_WAFER_ID': '2025-06-4:36:57:54_A12345678998999', 'PCM_SITE': '4', 'VALUE': 13},
        {'DATE_WAFER_ID': '2025-06-5:36:57:54_A12345678998999', 'PCM_SITE': '5', 'VALUE': 14},
        {'DATE_WAFER_ID': '2025-06-6:36:57:54_A12345678998999', 'PCM_SITE': '1', 'VALUE': 11},
        {'DATE_WAFER_ID': '2025-06-7:36:57:54_A12345678998999', 'PCM_SITE': '2', 'VALUE': 12},
        {'DATE_WAFER_ID': '2025-06-8:36:57:54_A12345678998999', 'PCM_SITE': '3', 'VALUE': 13},
        {'DATE_WAFER_ID': '2025-06-9:36:57:54_A12345678998999', 'PCM_SITE': '4', 'VALUE': 14},
        {'DATE_WAFER_ID': '2025-06-10:36:57:54_A12345678998999', 'PCM_SITE': '5', 'VALUE': 15},
        {'DATE_WAFER_ID': '2025-06-11:36:57:54_A12345678998999', 'PCM_SITE': '1', 'VALUE': 10},
        {'DATE_WAFER_ID': '2025-06-12:36:57:54_A12345678998999', 'PCM_SITE': '2', 'VALUE': 11},
        {'DATE_WAFER_ID': '2025-06-13:36:57:54_A12345678998999', 'PCM_SITE': '3', 'VALUE': 12},
        {'DATE_WAFER_ID': '2025-06-14:36:57:54_A12345678998999', 'PCM_SITE': '4', 'VALUE': 13},
        {'DATE_WAFER_ID': '2025-06-15:36:57:54_A12345678998999', 'PCM_SITE': '5', 'VALUE': 14},
        {'DATE_WAFER_ID': '2025-06-16:36:57:54_A12345678998999', 'PCM_SITE': '1', 'VALUE': 12},
        {'DATE_WAFER_ID': '2025-06-17:36:57:54_A12345678998999', 'PCM_SITE': '2', 'VALUE': 13},
        {'DATE_WAFER_ID': '2025-06-18:36:57:54_A12345678998999', 'PCM_SITE': '3', 'VALUE': 14},
        {'DATE_WAFER_ID': '2025-06-19:36:57:54_A12345678998999', 'PCM_SITE': '4', 'VALUE': 15},
        {'DATE_WAFER_ID': '2025-06-20:36:57:54_A12345678998999', 'PCM_SITE': '5', 'VALUE': 16},
        {'DATE_WAFER_ID': '2025-06-21:36:57:54_A12345678998999', 'PCM_SITE': '1', 'VALUE': 14},
        {'DATE_WAFER_ID': '2025-06-22:36:57:54_A12345678998999', 'PCM_SITE': '2', 'VALUE': 13},
        {'DATE_WAFER_ID': '2025-06-23:36:57:54_A12345678998999', 'PCM_SITE': '3', 'VALUE': 13},
        {'DATE_WAFER_ID': '2025-06-24:36:57:54_A12345678998999', 'PCM_SITE': '4', 'VALUE': 12},
        {'DATE_WAFER_ID': '2025-06-25:36:57:54_A12345678998999', 'PCM_SITE': '5', 'VALUE': 11},
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
    
    # 백엔드에서 질의 분석 (choice 파라미터는 무시하고 백엔드가 결정)
    detected_type, command_type, error_msg = analyze_query(message)
    
    if error_msg:
        # 실패한 메시지는 저장하지 않고 에러만 반환
        yield f"data: {json.dumps({'msg': error_msg})}\n\n"
        return
    
    # 사용자 메시지 시간 기록
    user_message_time = datetime.now()
    
    # 유효한 메시지만 저장
    user_message = chat_storage.add_message(chatroom_id, message, 'user', detected_type)
    
    # 처리 중 메시지 (저장하지 않고 프론트엔드에서만 표시)
    yield f"data: {json.dumps({'status': 'processing'})}\n\n"
    await asyncio.sleep(0.5)
    
    # 백엔드가 결정한 데이터 타입별 처리
    if detected_type == 'pcm':
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
    
    elif detected_type == 'cp':
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
    
    elif detected_type == 'rag':
        # RAG 처리 - 백엔드에서 완전히 결정
        if command_type == 'search':
            # 파일 검색 결과 반환
            answer = generate_rag_answer_data()
            response = {
                'result': 'rag',
                'files': answer,  # 파일 리스트
                'response': None,
                'timestamp': datetime.now().isoformat()
            }
        else:
            # 일반적인 질문에 대한 텍스트 응답
            response = {
                'result': 'rag',
                'files': None,
                'response': f"'{message}'에 대한 답변입니다. 요청하신 내용을 분석하여 적절한 정보를 제공드립니다.",
                'timestamp': datetime.now().isoformat()
            }
    
    # 성공한 경우에만 저장
    bot_response = chat_storage.add_response(user_message.id, chatroom_id, response)
    
    # real_data를 제외한 response 데이터 생성 (채팅 히스토리용)
    history_response = response.copy()
    if 'real_data' in history_response:
        del history_response['real_data']
    
    print(f"📝 Saving to chat history (real_data excluded): {json.dumps(history_response, indent=2)}")
    print(f"📝 JSON string being saved: {json.dumps(history_response)}")
    
    # 봇 응답 시간 기록
    bot_response_time = datetime.now()
    
    # 채팅 히스토리에 추가 (real_data 제외) - 실제 시간 사용
    chat_history = chat_storage.add_chat_history(
        chatroom_id, 
        message, 
        json.dumps(history_response),
        user_time=user_message_time,
        response_time=bot_response_time
    )
    print(f"📝 Chat history saved with chat_id: {chat_history.chat_id}")
    print(f"📝 Bot response in chat history: {chat_history.bot_response}")
    print(f"📅 User message time: {user_message_time}, Bot response time: {bot_response_time}")
    
    # 성공 메시지는 저장하지 않음 (프론트엔드에서만 표시)
    # 실제 응답 데이터는 채팅 히스토리에만 저장
    
    # 최종 응답 - 실제 chat_id 사용
    chat_response = {
        'chat_id': chat_history.chat_id,  # 실제 생성된 chat_id 사용
        'message_id': user_message.id,
        'response_id': bot_response.id,
        'response': response
    }
    
    print(f"📤 Sending chat response with chat_id: {chat_history.chat_id}")
    
    # 응답 데이터 크기 확인
    response_json = json.dumps(chat_response)
    print(f"📤 Response JSON size: {len(response_json)} characters")
    
    # real_data 크기 확인
    if 'real_data' in response and response['real_data']:
        real_data_size = len(json.dumps(response['real_data']))
        print(f"📤 Real data size: {real_data_size} characters")
        print(f"📤 Real data records: {len(response['real_data'])}")
    
    yield f"data: {response_json}\n\n"

@app.post("/chatrooms")
async def create_chatroom():
    """새 채팅방 생성 (파라미터 없음)"""
    try:
        chatroom = chat_storage.create_chatroom()
        return chatroom  # 직접 chatroom 객체 반환
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅방 생성 실패: {str(e)}")

@app.get("/chatrooms")
async def get_chatrooms():
    """모든 채팅방 조회 (API 명세에 맞는 형식)"""
    try:
        print(f"🔍 Getting all chatrooms. Total chatrooms in storage: {len(chat_storage.chatrooms)}")
        chatrooms = chat_storage.get_all_chatrooms()
        print(f"📋 Returning {len(chatrooms)} chatrooms: {chatrooms}")
        return {"chatrooms": chatrooms}
    except Exception as e:
        print(f"❌ Error getting chatrooms: {e}")
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


@app.delete("/chatrooms/{chatroom_id}")
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

@app.post("/chat")
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
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/edit_message")
async def edit_message_endpoint(request: EditMessageRequest):
    """메시지 수정 API 엔드포인트"""
    try:
        # 기존 chat_id 재사용 (새로운 chat_id 생성하지 않음)
        existing_chat_id = request.original_chat_id
        print(f"🔧 Using existing chat_id: {existing_chat_id}")
        
        # 백엔드에서 질의 분석 (choice 파라미터는 무시하고 백엔드가 결정)
        detected_type, command_type, error_msg = analyze_query(request.message)
        print(f"🔍 Edit message analysis - Type: {detected_type}, Command: {command_type}, Error: {error_msg}")
        
        if error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 데이터 타입별 처리 (기존 process_chat_request 로직과 동일)
        if detected_type == 'pcm':
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
        
        elif detected_type == 'cp':
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
        
        elif detected_type == 'rag':
            # RAG 처리 - 백엔드에서 완전히 결정
            if command_type == 'search':
                # 파일 검색 결과 반환
                answer = generate_rag_answer_data()
                response = {
                    'result': 'rag',
                    'files': answer,  # 파일 리스트
                    'response': None,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # 일반적인 질문에 대한 텍스트 응답
                response = {
                    'result': 'rag',
                    'files': None,
                    'response': f"'{request.message}'에 대한 답변입니다. 요청하신 내용을 분석하여 적절한 정보를 제공드립니다.",
                    'timestamp': datetime.now().isoformat()
                }
        
        # 응답 저장 (message_id 대신 chat_id 사용)
        response_id = str(uuid.uuid4())
        bot_response = BotResponse(
            id=response_id,
            message_id=str(existing_chat_id),  # chat_id를 message_id로 사용
            chatroom_id=request.chatroom_id,
            content=response,
            timestamp=datetime.now()
        )
        chat_storage.responses[response_id] = bot_response
        
        # real_data를 제외한 response 데이터 생성 (채팅 히스토리용)
        history_response = response.copy()
        if 'real_data' in history_response:
            del history_response['real_data']
        
        # 기존 chat_id를 사용하여 히스토리 업데이트
        existing_history = chat_storage.edit_chat_history(
            request.chatroom_id, 
            existing_chat_id, 
            request.message, 
            json.dumps(history_response)
        )
        
        if not existing_history:
            # 기존 히스토리가 없으면 새로 생성 (기존 chat_id 사용)
            existing_history = chat_storage.add_chat_history(
                request.chatroom_id,
                request.message,
                json.dumps(history_response),
                user_time=datetime.now(),
                response_time=datetime.now()
            )
            # 새로 생성된 히스토리의 chat_id를 기존 chat_id로 변경
            existing_history.chat_id = existing_chat_id
            print(f"✅ Created new chat history with existing chat_id: {existing_chat_id}")
        
        # 응답 데이터 확인
        print(f"📤 Edit response contains real_data: {'real_data' in response}")
        if 'real_data' in response:
            print(f"📤 Real data records: {len(response['real_data'])}")
            print(f"📤 Real data sample: {response['real_data'][:2] if len(response['real_data']) > 0 else 'empty'}")
        
        final_response = {
            'success': True,
            'message': '메시지가 성공적으로 수정되었습니다.',
            'chat_id': existing_chat_id,  # 기존 chat_id 반환
            'response_id': bot_response.id,
            'response': response
        }
        
        print(f"📤 Final response keys: {list(final_response.keys())}")
        print(f"📤 Response keys: {list(response.keys())}")
        
        return final_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메시지 수정 실패: {str(e)}")

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