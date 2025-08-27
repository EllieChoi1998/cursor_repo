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

# 전역 변수로 마스킹된 데이터프레임 저장
masking_df = None

def load_masking_data(excel_name: str = 'masking_df.xlsx') -> bool:
    """마스킹된 엑셀 데이터 로드"""
    global masking_df
    try:
        masking_df = pd.read_excel(excel_name)
        print(f"📊 마스킹 데이터 로드 완료: {masking_df.shape[0]}행 {masking_df.shape[1]}열")
        print(f"📊 컬럼 목록: {list(masking_df.columns)}")
        return True
    except FileNotFoundError:
        print("⚠️ masking_df.xlsx 파일을 찾을 수 없습니다. 샘플 데이터를 사용합니다.")
        return False
    except Exception as e:
        print(f"❌ 마스킹 데이터 로드 오류: {e}")
        return False

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
    name: str  # 채팅방 이름 추가

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
    data_type: str  # 'pcm', 'inline', 'rag'

# 응답 모델
class BotResponse(BaseModel):
    id: str
    message_id: str  # 연결된 사용자 메시지 ID
    chatroom_id: int  # 정수로 변경
    content: Dict[str, Any]
    timestamp: datetime

# 요청 모델
class ChatRequest(BaseModel):
    choice: str  # 'pcm', 'inline', 'rag'
    message: str
    chatroom_id: int  # 정수로 변경

# 메시지 수정 요청 모델 (새로 추가)
class EditMessageRequest(BaseModel):
    choice: str  # 'pcm', 'inline', 'rag'
    message: str
    chatroom_id: int
    original_chat_id: int  # 기존 chat_id

# 채팅방 생성 요청 모델 제거 (파라미터 없음)

# 채팅방 이름 수정 요청 모델 (새로 추가)
class UpdateChatRoomNameRequest(BaseModel):
    name: str

# 채팅방 목록 응답 모델 (API 명세에 맞게 수정)
class ChatRoomListItem(BaseModel):
    id: int
    name: str  # name 필드 추가
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
            id=chatroom_id,
            name=f"채팅방 #{chatroom_id}"  # 기본 이름 설정
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
                name=chatroom.name,  # name 필드 추가
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

    def update_chatroom_name(self, chatroom_id: int, name: str) -> Optional[ChatRoom]:
        """채팅방 이름 수정"""
        if chatroom_id in self.chatrooms:
            self.chatrooms[chatroom_id].name = name
            return self.chatrooms[chatroom_id]
        return None

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
        
        chat_storage.add_message(general_room.id, '안녕하세요! 데이터 분석 채팅 어시스턴트입니다. PCM, INLINE, RAG 분석에 대해 질문해주세요.', 'bot', 'pcm')
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

def initialize_application():
    """애플리케이션 초기화"""
    print("🚀 애플리케이션 초기화 시작...")
    
    # 기본 채팅방 생성
    initialize_default_chatrooms()
    
    print("✅ 애플리케이션 초기화 완료")

# 앱 시작 시 초기화
initialize_application()

# 데이터 타입별 지원되는 명령어
SUPPORTED_COMMANDS = {
    'pcm': {
        'trend': ['trend', '트렌드', '차트', '그래프', '분석'],
        'commonality': ['commonality', '커먼', '공통', '분석'],
        'point': ['point', '포인트', 'site', '사이트']
    },
    'inline': {
        'analysis': ['analysis', '분석', '성능', '모니터링'],
        'performance': ['performance', '성능', '측정', '평가']
    },
    'rag': {
        'search': ['search', '검색', '찾기', '조회'],
        'summary': ['summary', '요약', '정리', '개요']
    }
}

def analyze_query_with_choice(choice: str, message: str) -> tuple[str, str, str]:
    """
    choice와 메시지를 함께 분석하여 어떤 타입의 처리가 필요한지 결정
    choice가 우선적으로 고려됨
    Returns: (data_type, command_type, error_message)
    """
    message_lower = message.lower().strip()
    choice_lower = choice.lower().strip() if choice else ""
    
    # 빈 메시지 체크
    if not message_lower:
        return "", "", "메시지를 입력해주세요."
    
    # choice가 'pcm'인 경우
    if choice_lower == 'pcm':
        return analyze_pcm_query(message_lower)
    
    # choice가 'inline'인 경우
    elif choice_lower == 'inline':
        return analyze_inline_query(message_lower)
    
    # choice가 'rag'인 경우
    elif choice_lower == 'rag':
        return analyze_rag_query(message_lower)
    
    # choice가 없거나 인식되지 않은 경우 기존 analyze_query 로직 사용
    else:
        return analyze_query(message_lower)

def analyze_pcm_query(message_lower: str) -> tuple[str, str, str]:
    """PCM choice에 대한 메시지 분석"""
    # Two Tables 키워드 우선 검사 (PCM choice + 'two' 메시지)
    if 'two' in message_lower:
        # 테스트 시나리오 체크
        if 'empty' in message_lower:
            if 'lot' in message_lower and 'pe' not in message_lower:
                return 'two', 'two_tables_empty_lot', ""
            elif 'pe' in message_lower and 'lot' not in message_lower:
                return 'two', 'two_tables_empty_pe', ""
            else:
                return 'two', 'two_tables_empty_both', ""
        return 'two', 'two_tables', ""
    
    # sameness_to_trend, commonality_to_trend 키워드 검사 (가장 구체적인 키워드부터 먼저 검사)
    elif 'sameness_to_trend' in message_lower:
        return 'pcm', 'sameness_to_trend', ""
    elif 'commonality_to_trend' in message_lower:
        return 'pcm', 'commonality_to_trend', ""
    elif 'to_trend' in message_lower:
        return 'pcm', 'to_trend', ""
    elif any(k in message_lower for k in ['trend', '트렌드', '차트', '그래프']):
        return 'pcm', 'trend', ""
    elif any(k in message_lower for k in ['commonality', '커먼', '공통']):
        return 'pcm', 'commonality', ""
    elif any(k in message_lower for k in ['sameness']):
        return 'pcm', 'sameness', ""
    elif any(k in message_lower for k in ['point', '포인트', 'site', '사이트']):
        return 'pcm', 'point', ""
    else:
        return 'pcm', 'trend', ""  # 기본값

def analyze_inline_query(message_lower: str) -> tuple[str, str, str]:
    """INLINE choice에 대한 메시지 분석"""
    if any(k in message_lower for k in ['initial', '초기', '처음']):
        return 'inline', 'trend_initial', ""
    elif any(k in message_lower for k in ['followup', 'follow-up', '후속', '팔로우', 'para', 'eq_cham']):
        return 'inline', 'trend_followup', ""
    elif any(k in message_lower for k in ['performance', '성능', '모니터링']):
        return 'inline', 'performance', ""
    else:
        return 'inline', 'analysis', ""

def analyze_rag_query(message_lower: str) -> tuple[str, str, str]:
    """RAG choice에 대한 메시지 분석"""
    rag_keywords = ['검색', 'search', '찾기', '조회', '문서', 'document', '파일', 'file']
    for keyword in rag_keywords:
        if keyword in message_lower:
            return 'rag', 'search', ""
    return 'rag', 'general', ""

def analyze_query(message: str) -> tuple[str, str, str]:
    """
    메시지를 분석하여 어떤 타입의 처리가 필요한지 결정
    Returns: (data_type, command_type, error_message)
    """
    message_lower = message.lower().strip()
    
    # 빈 메시지 체크
    if not message_lower:
        return "", "", "메시지를 입력해주세요."
    
    # Two Tables 키워드는 choice='two'일 때만 처리하므로 여기서는 제거
    
    # RAG 관련 키워드 우선 검사
    rag_keywords = ['검색', 'search', '찾기', '조회', '문서', 'document', '파일', 'file', '설명', '요약', 'summary']
    for keyword in rag_keywords:
        if keyword in message_lower:
            return 'rag', 'search', ""
    
    # sameness_to_trend, commonality_to_trend 키워드 검사 (가장 구체적인 키워드부터 먼저 검사)
    if 'sameness_to_trend' in message_lower:
        return 'pcm', 'sameness_to_trend', ""
    elif 'commonality_to_trend' in message_lower:
        return 'pcm', 'commonality_to_trend', ""
    
    # PCM 관련 키워드 검사 (일반적인 키워드들은 나중에 검사)
    pcm_keywords = ['pcm', 'trend', '트렌드', '차트', '그래프', 'commonality', '커먼', '공통', 'sameness', 'point', '포인트', 'site', '사이트']
    for keyword in pcm_keywords:
        if keyword in message_lower:
            if any(k in message_lower for k in ['trend', '트렌드', '차트', '그래프']):
                return 'pcm', 'trend', ""
            elif any(k in message_lower for k in ['commonality', '커먼', '공통']):
                return 'pcm', 'commonality', ""
            elif any(k in message_lower for k in ['sameness']):
                return 'pcm', 'sameness', ""
            elif any(k in message_lower for k in ['point', '포인트', 'site', '사이트']):
                return 'pcm', 'point', ""
            else:
                return 'pcm', 'trend', ""  # 기본값
    
    # INLINE 관련 키워드 검사
    inline_keywords = ['inline', 'trend', 'edit']
    for keyword in inline_keywords:
        if keyword in message_lower:
            if any(k in message_lower for k in ['trend']):
                return 'inline', 'trend', ""
            else:
                return 'inline', 'edit', ""
    
    # 기본적으로 RAG로 처리 (질문이나 일반적인 요청)
    return 'rag', 'general', ""

def generate_pcm_trend_data() -> list:
    """PCM 트렌드 데이터 생성"""
    data = {}
    para_list = ["PARA1", "PARA2"]
    for para in para_list:
        single = []
        for i in range(1, 1000):
            single.append({
                'DATE_WAFER_ID': f'2025-06-{i}:36:57:54_A12345678998999',
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
        data[para]=single
    return data

def generate_commonality_data() -> tuple[list, dict]:
    """Commonality 데이터 생성"""
    # 테이블용 배열 데이터 생성 (PCM 트렌드 데이터를 배열로 변환)
    pcm_data = generate_pcm_trend_data()
    
    print(f"🔍 generate_commonality_data: pcm_data type = {type(pcm_data)}")
    print(f"🔍 generate_commonality_data: pcm_data keys = {list(pcm_data.keys()) if isinstance(pcm_data, dict) else 'not dict'}")
    
    # PARA별 객체를 배열로 변환
    table_data = []
    for para_name, para_data in pcm_data.items():
        for row in para_data:
            table_data.append({
                **row,
                'PARA': para_name
            })
    
    print(f"🔍 generate_commonality_data: table_data type = {type(table_data)}")
    print(f"🔍 generate_commonality_data: table_data length = {len(table_data)}")
    print(f"🔍 generate_commonality_data: table_data sample = {table_data[:2] if table_data else 'empty'}")
    
    # Commonality 정보
    commonality = {
        'good_lots': ['LOT001', 'LOT002', 'LOT003'],
        'bad_lots': ['LOT004', 'LOT005'],
        'good_wafers': ['WAFER001', 'WAFER002', 'WAFER003'],
        'bad_wafers': ['WAFER004', 'WAFER005']
    }
    
    return table_data, commonality

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

def generate_inline_analysis_data() -> list:
    """INLINE 분석 데이터 생성"""
    # 마스킹된 엑셀 데이터 로드 시도
    load_masking_data(excel_name='iqc_data.xlsx')
    global masking_df

    # 실제 엑셀 데이터가 있으면 사용
    if masking_df is not None and not masking_df.empty:
        print("📊 실제 마스킹 데이터 사용")
        data = masking_df.to_dict(orient='records')
        return data
    
    print("📊 샘플 데이터 생성 (엑셀 파일 없음)")
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

def generate_inline_trend_initial_data() -> list:
    """INLINE Trend Initial 데이터 생성 (DEVICE 기준)"""
    load_masking_data(excel_name='iqc_data.xlsx')
    global masking_df

    # 실제 엑셀 데이터가 있으면 사용
    if masking_df is not None and not masking_df.empty:
        try:
            print("📊 실제 마스킹 데이터 사용")
            
            # 데이터프레임 복사 후 정리
            df_clean = masking_df.copy()
            
            # 1. datetime/timestamp 컬럼들을 문자열로 변환
            for col in df_clean.columns:
                if df_clean[col].dtype == 'datetime64[ns]' or pd.api.types.is_datetime64_any_dtype(df_clean[col]):
                    df_clean[col] = df_clean[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                    print(f"📅 날짜 컬럼 변환: {col}")
            
            # 2. NaN 값들을 None으로 변환
            df_clean = df_clean.where(pd.notnull(df_clean), None)
            
            # 3. numpy 타입들을 Python 기본 타입으로 변환
            for col in df_clean.columns:
                if df_clean[col].dtype == 'int64':
                    df_clean[col] = df_clean[col].astype('int')
                elif df_clean[col].dtype == 'float64':
                    df_clean[col] = df_clean[col].astype('float')
            
            # 딕셔너리로 변환
            data = df_clean.to_dict(orient='records')
            print(f"✅ 데이터 변환 완료: {len(data)}개 레코드")
            return data
            
        except Exception as e:
            print(f"❌ 실제 데이터 처리 오류: {e}")
            print("📊 샘플 데이터로 대체합니다.")
    
    # 샘플 데이터 생성
    data = []
    for i in range(1, 21):
        data.append({
            'key': str(i),
            'NO_VAL1': round(random.uniform(350, 450), 3),
            'NO_VAL2': round(random.uniform(400, 500), 3), 
            'NO_VAL3': round(random.uniform(450, 550), 3),
            'DEVICE': random.choice(['DEVICE_A', 'DEVICE_B', 'DEVICE_C']),
            'USL': 550,
            'LSL': 300,
            'TGT': 420
        })
    return data

def generate_inline_trend_followup_data(criteria: str) -> list:
    """INLINE Trend Followup 데이터 생성 (다양한 criteria 기준)"""
    load_masking_data(excel_name='iqc_data.xlsx')
    global masking_df

    # 실제 엑셀 데이터가 있으면 사용
    if masking_df is not None and not masking_df.empty:
        print("📊 실제 마스킹 데이터 사용")
        data = masking_df.to_dict(orient='records')
        return data
    data = []
    
    # criteria에 따라 다른 데이터 생성
    if criteria == "PARA":
        para_values = ['PARA_X', 'PARA_Y', 'PARA_Z']
        criteria_key = 'PARA'
        criteria_values = para_values
    elif criteria == "EQ_CHAM":
        eq_cham_values = ['P0', 'P1', 'P2', 'P3']
        criteria_key = 'EQ_CHAM'
        criteria_values = eq_cham_values
    else:
        # 기타 criteria의 경우
        criteria_key = criteria
        criteria_values = [f'{criteria}_A', f'{criteria}_B', f'{criteria}_C']
    
    for i in range(1, 21):
        data.append({
            'key': str(i),
            'NO_VAL1': round(random.uniform(350, 450), 3),
            'NO_VAL2': round(random.uniform(400, 500), 3),
            'NO_VAL3': round(random.uniform(450, 550), 3),
            criteria_key: random.choice(criteria_values),
            'USL': 550,
            'LSL': 300,
            'TGT': 420
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

def generate_pcm_to_trend_data() -> dict:
    """PCM To Trend 데이터 생성 (실제 마스킹된 엑셀 데이터 또는 샘플 데이터 사용)"""
    # 마스킹된 엑셀 데이터 로드 시도
    load_masking_data(excel_name='masking_df.xlsx')
    
    global masking_df
    
    
    # 실제 엑셀 데이터가 있으면 사용
    if masking_df is not None and not masking_df.empty:
        print("📊 실제 마스킹 데이터 사용")
        data = {}
        
        # PARA 컬럼이 있는지 확인
        if 'PARA' in masking_df.columns:
            # PARA별로 데이터 그룹화
            para_groups = masking_df.groupby('PARA')
            for para_name, para_data in para_groups:
                # 데이터프레임을 딕셔너리 리스트로 변환
                data[para_name] = para_data.to_dict('records')
                print(f"📊 PARA {para_name}: {len(para_data)}개 레코드")
        else:
            # PARA 컬럼이 없으면 전체 데이터를 하나의 그룹으로 처리
            data['ALL_DATA'] = masking_df.to_dict('records')
            print(f"📊 전체 데이터: {len(masking_df)}개 레코드")
        
        return data
    
    # 엑셀 파일이 없으면 샘플 데이터 생성
    print("📊 샘플 데이터 생성 (엑셀 파일 없음)")
    data = {}
    para_list = ["PARA_A", "PARA_B", "PARA_C"]
    route_list = ["route1", "route2", "route3"]
    oper_list = ["oper1", "oper2", "oper3", "oper4"]
    
    for para in para_list:
        single = []
        for i in range(1, 16):  # 15개 스텝 데이터 생성
            # 실제 데이터 구조와 동일한 범위로 값 생성
            min_val = round(random.uniform(350, 450), 4)
            max_val = round(random.uniform(600, 700), 4)
            q1_val = round(random.uniform(min_val + 30, min_val + 80), 4)
            q2_val = round(random.uniform(q1_val + 30, q1_val + 80), 4)
            q3_val = round(random.uniform(q2_val + 30, max_val - 30), 4)
            
            single.append({
                # 마스킹된 컬럼들 (실제로는 ID나 인덱스 정보)
                'Unnamed: 0.1': i,  # 마스킹된 컬럼 1
                'Unnamed: 0': i,    # 마스킹된 컬럼 2
                
                # 실제 데이터 컬럼들
                'key': f'{i}',  # 실제 데이터에서는 숫자 형태
                'MAIN_ROUTE_DESC': random.choice(route_list),
                'MAIN_OPER_DESC': random.choice(oper_list),
                'EQ_CHAM': random.choice(['P0', 'P1', 'P2']),
                'PARA': para,
                
                # 통계값들 (실제 데이터 범위 반영)
                'MIN': min_val,
                'MAX': max_val,
                'Q1': q1_val,
                'Q2': q2_val,
                'Q3': q3_val,
                
                # 제어선들 (실제 데이터 범위 반영)
                'USL': 550,
                'TGT': 420,
                'LSL': 300,
                'UCL': 500,
                'LCL': 360
            })
        data[para] = single
    
    # PARA별로 분리된 데이터 반환
    return data

def generate_two_tables_data(test_empty_scenario: str = None) -> dict:
    """Two Tables 데이터 생성 - 서로 다른 컬럼과 데이터를 가진 두 개의 테이블"""
    # 마스킹된 엑셀 데이터 로드 시도
    load_masking_data(excel_name='masking_df.xlsx')
    global masking_df
    
    # 첫 번째 테이블: Lot Hold 데이터 (가상의 lot hold 정보)
    lot_hold_data = []
    for i in range(1, 16):
        lot_hold_data.append({
            'LOT_ID': f'LOT_{i:03d}',
            'HOLD_REASON': random.choice(['QUALITY_ISSUE', 'EQUIPMENT_MAINT', 'MATERIAL_SHORTAGE', 'PROCESS_DEVIATION']),
            'HOLD_DATE': f'2024-12-{random.randint(1, 31):02d}',
            'HOLD_STATUS': random.choice(['ACTIVE', 'RELEASED', 'CANCELLED']),
            'PRIORITY': random.choice(['HIGH', 'MEDIUM', 'LOW']),
            'WAFER_COUNT': random.randint(10, 25),
            'AFFECTED_STEP': random.choice(['PHOTO', 'ETCH', 'DIFFUSION', 'METAL']),
            'OWNER': random.choice(['ENGINEER_A', 'ENGINEER_B', 'ENGINEER_C'])
        })
    
    # 두 번째 테이블: PE Confirm Module 데이터 (가상의 PE 확인 모듈 정보)
    pe_confirm_data = []
    for i in range(1, 12):  # 다른 개수로 설정
        pe_confirm_data.append({
            'MODULE_ID': f'PE_MOD_{i:02d}',
            'CONFIRM_STATUS': random.choice(['CONFIRMED', 'PENDING', 'REJECTED']),
            'CONFIRM_DATE': f'2024-12-{random.randint(1, 31):02d}',
            'PARAMETER_NAME': random.choice(['TEMPERATURE', 'PRESSURE', 'FLOW_RATE', 'POWER']),
            'TARGET_VALUE': round(random.uniform(100, 500), 2),
            'ACTUAL_VALUE': round(random.uniform(95, 505), 2),
            'TOLERANCE': round(random.uniform(5, 15), 1),
            'RESULT': random.choice(['PASS', 'FAIL', 'WARNING']),
            'INSPECTOR': random.choice(['INSPECTOR_X', 'INSPECTOR_Y', 'INSPECTOR_Z'])
        })
    
    # 실제 엑셀 데이터가 있으면 첫 번째 테이블에 활용
    if masking_df is not None and not masking_df.empty:
        # 실제 데이터의 일부를 첫 번째 테이블로 사용 (최대 10개 레코드)
        sample_size = min(10, len(masking_df))
        lot_hold_data = masking_df.head(sample_size).to_dict('records')
        print(f"📊 Using real data for lot_hold: {sample_size} records")
    
    # 테스트 시나리오 처리 (특별한 경우에만)
    if test_empty_scenario:
        if test_empty_scenario == 'empty_lot_hold':
            lot_hold_data = []
            print("🔄 Test scenario: Empty lot_hold data")
        elif test_empty_scenario == 'empty_pe_confirm':
            pe_confirm_data = []
            print("🔄 Test scenario: Empty pe_confirm data")
        elif test_empty_scenario == 'both_empty':
            lot_hold_data = []
            pe_confirm_data = []
            print("🔄 Test scenario: Both tables empty")
    
    print(f"📊 Generated data - Lot Hold: {len(lot_hold_data)} records, PE Confirm: {len(pe_confirm_data)} records")
    
    return {
        "result": "lot_hold_pe_confirm_module",
        "real_data": [
            {"lot_hold_module": lot_hold_data},
            {"pe_confirm_module": pe_confirm_data}
        ]
    }

async def process_chat_request(choice: str, message: str, chatroom_id: int):
    """채팅 요청 처리"""
    # 채팅방 확인
    chatroom = chat_storage.get_chatroom(chatroom_id)
    if not chatroom:
        yield f"data: {json.dumps({'msg': '존재하지 않는 채팅방입니다.'})}\n\n"
        return
    
    # choice 파라미터를 우선적으로 고려하여 질의 분석
    detected_type, command_type, error_msg = analyze_query_with_choice(choice, message)
    
    print(f"🔍 DEBUG: choice='{choice}', message='{message}'")
    print(f"🔍 DEBUG: detected_type='{detected_type}', command_type='{command_type}', error_msg='{error_msg}'")
    
    if error_msg:
        # 실패한 메시지는 저장하지 않고 에러만 반환
        yield f"data: {json.dumps({'msg': error_msg})}\n\n"
        return
    
    # 사용자 메시지 시간 기록
    user_message_time = datetime.now()
    
    # 유효한 메시지만 저장
    user_message = chat_storage.add_message(chatroom_id, message, 'user', detected_type)
    
    # 처리 시작 메시지
    yield f"data: {json.dumps({'progress_message': '🔄 메시지를 처리하는 중...'})}\n\n"
    await asyncio.sleep(0.3)
    
    # 분석 시작 메시지
    yield f"data: {json.dumps({'progress_message': '⚙️ 데이터를 분석하고 있습니다...'})}\n\n"
    await asyncio.sleep(0.2)
    
    # 백엔드가 결정한 데이터 타입별 처리
    if detected_type == 'pcm':
        if command_type == 'trend':
            # PCM 트렌드 데이터 생성 중 메시지
            yield f"data: {json.dumps({'progress_message': '📈 PCM TREND 데이터를 생성하고 있습니다...'})}\n\n"
            await asyncio.sleep(0.3)
            
            data = generate_pcm_trend_data()
            
            # 성공 메시지 생성 (Chart Summary 포함)
            total_records = len(data) if isinstance(data, list) else 0
            device_types = []
            date_range = "N/A"
            
            if isinstance(data, list) and len(data) > 0:
                # Device types 추출
                device_types = list(set(row.get('DEVICE', 'Unknown') for row in data if isinstance(row, dict)))
                # Date range 추출  
                date_ids = [row.get('DATE_WAFER_ID', 0) for row in data if isinstance(row, dict) and row.get('DATE_WAFER_ID')]
                if date_ids:
                    date_range = f"{min(date_ids)} - {max(date_ids)}"
            
            success_message = f"✅ PCM TREND 데이터를 성공적으로 받았습니다!\n• Result Type: lot_start\n• Total Records: {total_records}\n• Chat ID: {chatroom_id}\n\nChart Summary:\n• Device Types: {', '.join(device_types) if device_types else 'N/A'}\n• Date Range: {date_range}"
            
            response = {
                'result': 'lot_start',
                'real_data': data,
                'sql': 'SELECT * FROM pcm_data WHERE date >= "2024-01-01" ORDER BY date_wafer_id',
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }
        elif command_type == 'commonality':
            # commonality 데이터 생성 중 메시지
            yield f"data: {json.dumps({'progress_message': '📊 COMMONALITY 데이터를 생성하고 있습니다...'})}\n\n"
            await asyncio.sleep(0.3)
            
            # commonality 처리 (DynamicTable.vue 사용)
            data, commonality_info = generate_commonality_data()
            
            # 성공 메시지 생성
            success_message = f"✅ COMMONALITY 데이터를 성공적으로 받았습니다!\n• Result Type: commonality\n• Total Records: {len(data) if isinstance(data, list) else sum(len(v) if isinstance(v, list) else 0 for v in data.values()) if isinstance(data, dict) else 0}\n• Chat ID: {chatroom_id}"
            
            response = {
                'result': 'commonality',
                'real_data': data,
                'commonality_info': commonality_info,
                'sql': 'SELECT * FROM pcm_data WHERE type = "commonality"',
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }
        elif command_type == 'sameness':
            # sameness 데이터 생성 중 메시지
            yield f"data: {json.dumps({'progress_message': '📊 SAMENESS 데이터를 생성하고 있습니다...'})}\n\n"
            await asyncio.sleep(0.3)
            
            # sameness 처리 (DynamicTable.vue 사용)
            data, _ = generate_commonality_data()  # sameness도 동일한 데이터 구조 사용
            
            # 성공 메시지 생성
            success_message = f"✅ SAMENESS 데이터를 성공적으로 받았습니다!\n• Result Type: sameness\n• Total Records: {len(data) if isinstance(data, list) else sum(len(v) if isinstance(v, list) else 0 for v in data.values()) if isinstance(data, dict) else 0}\n• Chat ID: {chatroom_id}"
            
            response = {
                'result': 'sameness',
                'real_data': data,
                'sql': 'SELECT * FROM pcm_data WHERE type = "sameness"',
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }
        elif command_type == 'point':
            # PCM 포인트 데이터 생성 중 메시지
            yield f"data: {json.dumps({'progress_message': '📍 PCM POINT 데이터를 생성하고 있습니다...'})}\n\n"
            await asyncio.sleep(0.3)
            
            data = generate_pcm_point_data()
            
            # 성공 메시지 생성 (Chart Summary 포함)
            total_records = len(data) if isinstance(data, list) else 0
            pcm_sites = []
            date_range = "N/A"
            
            if isinstance(data, list) and len(data) > 0:
                # PCM_SITE 추출
                pcm_sites = list(set(row.get('PCM_SITE', 'Unknown') for row in data if isinstance(row, dict)))
                # Date range 추출  
                date_ids = [row.get('DATE_WAFER_ID', 0) for row in data if isinstance(row, dict) and row.get('DATE_WAFER_ID')]
                if date_ids:
                    date_range = f"{min(date_ids)} - {max(date_ids)}"
            
            success_message = f"✅ PCM POINT 데이터를 성공적으로 받았습니다!\n• Result Type: lot_point\n• Total Records: {total_records}\n• Chat ID: {chatroom_id}\n\nChart Summary:\n• PCM Sites: {', '.join(pcm_sites) if pcm_sites else 'N/A'}\n• Date Range: {date_range}"
            
            response = {
                'result': 'lot_point',
                'real_data': data,
                'sql': 'SELECT * FROM pcm_data WHERE type = "point"',
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }
        elif command_type == 'sameness_to_trend':
            # sameness_to_trend 데이터 생성 중 메시지
            yield f"data: {json.dumps({'progress_message': '📈 SAMENESS TO TREND 데이터를 생성하고 있습니다...'})}\n\n"
            await asyncio.sleep(0.3)
            
            # sameness_to_trend 처리 (PCMToTrend.vue 사용)
            data = generate_pcm_to_trend_data()
            
            # 데이터 개수 계산
            total_records = 0
            if isinstance(data, list):
                total_records = len(data)
            elif isinstance(data, dict):
                total_records = sum(len(v) if isinstance(v, list) else 0 for v in data.values())
            
            # 성공 메시지 생성
            success_message = f"✅ SAMENESS TO TREND 데이터를 성공적으로 받았습니다!\n• Result Type: sameness_to_trend\n• Total Records: {total_records}\n• Chat ID: {chatroom_id}"
            
            response = {
                'result': 'sameness_to_trend',
                'real_data': data,
                'sql': 'SELECT * FROM pcm_to_trend WHERE type = "sameness"',
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }
        elif command_type == 'commonality_to_trend':
            # commonality_to_trend 데이터 생성 중 메시지
            yield f"data: {json.dumps({'progress_message': '📈 COMMONALITY TO TREND 데이터를 생성하고 있습니다...'})}\n\n"
            await asyncio.sleep(0.3)
            
            # commonality_to_trend 처리 (PCMToTrend.vue 사용)
            data = generate_pcm_to_trend_data()
            
            # 데이터 개수 계산
            total_records = 0
            if isinstance(data, list):
                total_records = len(data)
            elif isinstance(data, dict):
                total_records = sum(len(v) if isinstance(v, list) else 0 for v in data.values())
            
            # 성공 메시지 생성
            success_message = f"✅ COMMONALITY TO TREND 데이터를 성공적으로 받았습니다!\n• Result Type: commonality_to_trend\n• Total Records: {total_records}\n• Chat ID: {chatroom_id}"
            
            response = {
                'result': 'commonality_to_trend',
                'real_data': data,
                'sql': 'SELECT * FROM pcm_to_trend WHERE type = "commonality"',
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }
        elif command_type == 'to_trend':
            # PCM TO TREND 데이터 생성 중 메시지
            yield f"data: {json.dumps({'progress_message': '📈 PCM TO TREND 데이터를 생성하고 있습니다...'})}\n\n"
            await asyncio.sleep(0.3)
            
            data = generate_pcm_to_trend_data()
            
            # 데이터 개수 계산
            total_records = 0
            if isinstance(data, list):
                total_records = len(data)
            elif isinstance(data, dict):
                total_records = sum(len(v) if isinstance(v, list) else 0 for v in data.values())
            
            # 성공 메시지 생성
            success_message = f"✅ PCM TO TREND 데이터를 성공적으로 받았습니다!\n• Result Type: pcm_to_trend\n• Total Records: {total_records}\n• Chat ID: {chatroom_id}"
            
            response = {
                'result': 'pcm_to_trend',
                'real_data': data,
                'sql': 'SELECT * FROM pcm_to_trend WHERE date >= "2024-01-01"',
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }
    
    elif detected_type == 'two':
        if command_type in ['two_tables', 'two_tables_empty_lot', 'two_tables_empty_pe', 'two_tables_empty_both']:
            # Two Tables 데이터 생성 중 메시지
            yield f"data: {json.dumps({'progress_message': '📊 TWO TABLES 데이터를 생성하고 있습니다...'})}\n\n"
            await asyncio.sleep(0.3)
            
            # 테스트 시나리오 매핑
            test_scenario = None
            if command_type == 'two_tables_empty_lot':
                test_scenario = 'empty_lot_hold'
            elif command_type == 'two_tables_empty_pe':
                test_scenario = 'empty_pe_confirm'
            elif command_type == 'two_tables_empty_both':
                test_scenario = 'both_empty'
            
            data = generate_two_tables_data(test_scenario)
            
            # 각 테이블의 데이터 개수 계산
            lot_hold_count = 0
            pe_confirm_count = 0
            
            if 'real_data' in data and len(data['real_data']) >= 2:
                lot_hold_data = data['real_data'][0].get('lot_hold_module', [])
                pe_confirm_data = data['real_data'][1].get('pe_confirm_module', [])
                lot_hold_count = len(lot_hold_data) if isinstance(lot_hold_data, list) else 0
                pe_confirm_count = len(pe_confirm_data) if isinstance(pe_confirm_data, list) else 0
            
            # 성공 메시지 생성
            success_message = f"✅ TWO TABLES 데이터를 성공적으로 받았습니다!\n• Result Type: lot_hold_pe_confirm_module\n• Lot Hold Records: {lot_hold_count}\n• PE Confirm Records: {pe_confirm_count}\n• Chat ID: {chatroom_id}"
            
            response = {
                'result': 'lot_hold_pe_confirm_module',
                'real_data': data['real_data'],
                'sql': 'SELECT * FROM lot_hold_table, pe_confirm_table',
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }
    
    elif detected_type == 'inline':
        print(f"🎯 DEBUG: Processing inline type with command_type='{command_type}'")
        if command_type == 'trend_initial':
            # INLINE Trend Initial 데이터 생성 중 메시지
            yield f"data: {json.dumps({'progress_message': '📊 INLINE TREND INITIAL 데이터를 생성하고 있습니다...'})}\n\n"
            await asyncio.sleep(0.3)
            
            data = generate_inline_trend_initial_data()
            
            # 성공 메시지 생성
            success_message = f"✅ INLINE TREND INITIAL 데이터를 성공적으로 받았습니다!\n• Result Type: inline_trend_initial\n• Total Records: {len(data) if isinstance(data, list) else 0}\n• Chat ID: {chatroom_id}\n• Criteria: DEVICE"
            
            response = {
                'result': 'inline_trend_initial',
                'criteria': 'DEVICE',
                'real_data': json.dumps(data),
                'success_message': success_message
            }
            print(f"🎯 DEBUG: Created inline_trend_initial response: {response.keys()}")
        elif command_type == 'trend_followup':
            # INLINE Trend Followup 데이터 생성 중 메시지
            yield f"data: {json.dumps({'progress_message': '📊 INLINE TREND FOLLOWUP 데이터를 생성하고 있습니다...'})}\n\n"
            await asyncio.sleep(0.3)
            
            # 메시지에서 criteria 추출 (기본값: PARA)
            criteria = 'PARA'
            if 'eq_cham' in message.lower():
                criteria = 'EQ_CHAM'
            elif 'route' in message.lower():
                criteria = 'ROUTE'
            elif 'oper' in message.lower():
                criteria = 'OPER'
            
            data = generate_inline_trend_followup_data(criteria)
            
            # 성공 메시지 생성
            success_message = f"✅ INLINE TREND FOLLOWUP 데이터를 성공적으로 받았습니다!\n• Result Type: inline_trend_followup\n• Total Records: {len(data) if isinstance(data, list) else 0}\n• Chat ID: {chatroom_id}\n• Criteria: {criteria}"
            
            response = {
                'result': 'inline_trend_followup',
                'criteria': criteria,
                'real_data': json.dumps(data),
                'success_message': success_message
            }
        elif command_type == 'analysis':
            # INLINE 분석 데이터 생성 중 메시지
            yield f"data: {json.dumps({'progress_message': '🔬 INLINE ANALYSIS 데이터를 생성하고 있습니다...'})}\n\n"
            await asyncio.sleep(0.3)
            
            data = generate_inline_analysis_data()
            
            # 성공 메시지 생성
            success_message = f"✅ INLINE ANALYSIS 데이터를 성공적으로 받았습니다!\n• Result Type: inline_analysis\n• Total Records: {len(data) if isinstance(data, list) else 0}\n• Chat ID: {chatroom_id}"
            
            response = {
                'result': 'inline_analysis',
                'real_data': data,
                'sql': 'SELECT * FROM inline_data WHERE analysis_date >= "2024-01-01"',
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }
        elif command_type == 'performance':
            # INLINE 성능 데이터 생성 중 메시지
            yield f"data: {json.dumps({'progress_message': '⚡ INLINE PERFORMANCE 데이터를 생성하고 있습니다...'})}\n\n"
            await asyncio.sleep(0.3)
            
            data = generate_inline_analysis_data()
            
            # 성공 메시지 생성
            success_message = f"✅ INLINE PERFORMANCE 데이터를 성공적으로 받았습니다!\n• Result Type: inline_performance\n• Total Records: {len(data) if isinstance(data, list) else 0}\n• Chat ID: {chatroom_id}"
            
            response = {
                'result': 'inline_performance',
                'real_data': data,
                'sql': 'SELECT * FROM inline_performance WHERE date >= "2024-01-01"',
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }
    
    elif detected_type == 'rag':
        # RAG 데이터 검색 중 메시지
        yield f"data: {json.dumps({'progress_message': '🔍 RAG 데이터를 검색하고 있습니다...'})}\n\n"
        await asyncio.sleep(0.3)
        
        # RAG 처리 - 백엔드에서 완전히 결정
        if command_type == 'search':
            # 파일 검색 결과 반환
            answer = generate_rag_answer_data()
            
            # 성공 메시지 생성
            success_message = f"✅ RAG 파일 검색이 완료되었습니다!\n• Result Type: rag\n• Found Files: {len(answer) if isinstance(answer, list) else 0}\n• Chat ID: {chatroom_id}"
            
            response = {
                'result': 'rag',
                'files': answer,  # 파일 리스트
                'response': None,
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }
        else:
            # 일반적인 질문에 대한 텍스트 응답
            response_text = f"'{message}'에 대한 답변입니다. 요청하신 내용을 분석하여 적절한 정보를 제공드립니다."
            
            # 성공 메시지 생성
            success_message = f"✅ RAG 답변 생성이 완료되었습니다!\n• Result Type: rag\n• Response Length: {len(response_text)} characters\n• Chat ID: {chatroom_id}"
            
            response = {
                'result': 'rag',
                'files': None,
                'response': response_text,
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
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

@app.put("/chatrooms/{chatroom_id}/name")
async def update_chatroom_name(chatroom_id: int, request: UpdateChatRoomNameRequest):
    """채팅방 이름 수정"""
    try:
        updated_chatroom = chat_storage.update_chatroom_name(chatroom_id, request.name)
        if not updated_chatroom:
            raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
        
        return {"success": True, "message": "채팅방 이름이 수정되었습니다.", "chatroom": updated_chatroom}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅방 이름 수정 실패: {str(e)}")

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
        
        # choice 파라미터를 우선적으로 고려하여 질의 분석
        detected_type, command_type, error_msg = analyze_query_with_choice(request.choice, request.message)
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
            elif command_type == 'sameness_to_trend':
                # sameness_to_trend 처리 (PCMToTrend.vue 사용)
                data = generate_pcm_to_trend_data()
                response = {
                    'result': 'sameness_to_trend',
                    'real_data': data,
                    'sql': 'SELECT * FROM pcm_to_trend WHERE type = "sameness"',
                    'timestamp': datetime.now().isoformat()
                }
            elif command_type == 'commonality_to_trend':
                # commonality_to_trend 처리 (PCMToTrend.vue 사용)
                data = generate_pcm_to_trend_data()
                response = {
                    'result': 'commonality_to_trend',
                    'real_data': data,
                    'sql': 'SELECT * FROM pcm_to_trend WHERE type = "commonality"',
                    'timestamp': datetime.now().isoformat()
                }
            elif command_type == 'to_trend':
                data = generate_pcm_to_trend_data()
                response = {
                    'result': 'pcm_to_trend',
                    'real_data': data,
                    'sql': 'SELECT * FROM pcm_to_trend WHERE date >= "2024-01-01"',
                    'timestamp': datetime.now().isoformat()
                }
        
        elif detected_type == 'two':
            if command_type in ['two_tables', 'two_tables_empty_lot', 'two_tables_empty_pe', 'two_tables_empty_both']:
                # 테스트 시나리오 매핑
                test_scenario = None
                if command_type == 'two_tables_empty_lot':
                    test_scenario = 'empty_lot_hold'
                elif command_type == 'two_tables_empty_pe':
                    test_scenario = 'empty_pe_confirm'
                elif command_type == 'two_tables_empty_both':
                    test_scenario = 'both_empty'
                
                data = generate_two_tables_data(test_scenario)
                response = {
                    'result': 'lot_hold_pe_confirm_module',
                    'real_data': data['real_data'],
                    'sql': 'SELECT * FROM lot_hold_table, pe_confirm_table',
                    'timestamp': datetime.now().isoformat()
                }
        
        elif detected_type == 'inline':
            if command_type == 'trend_initial':
                data = generate_inline_trend_initial_data()
                response = {
                    'result': 'inline_trend_initial',
                    'criteria': 'DEVICE',
                    'real_data': json.dumps(data),
                    'success_message': f"✅ INLINE TREND INITIAL 데이터를 성공적으로 받았습니다! (Edit Mode)"
                }
            elif command_type == 'trend_followup':
                # 메시지에서 criteria 추출 (기본값: PARA)
                criteria = 'PARA'
                if 'eq_cham' in request.message.lower():
                    criteria = 'EQ_CHAM'
                elif 'route' in request.message.lower():
                    criteria = 'ROUTE'
                elif 'oper' in request.message.lower():
                    criteria = 'OPER'
                
                data = generate_inline_trend_followup_data(criteria)
                response = {
                    'result': 'inline_trend_followup',
                    'criteria': criteria,
                    'real_data': json.dumps(data),
                    'success_message': f"✅ INLINE TREND FOLLOWUP 데이터를 성공적으로 받았습니다! (Edit Mode)"
                }
            elif command_type == 'analysis':
                data = generate_inline_analysis_data()
                response = {
                    'result': 'inline_analysis',
                    'real_data': data,
                    'sql': 'SELECT * FROM inline_data WHERE analysis_date >= "2024-01-01"',
                    'timestamp': datetime.now().isoformat()
                }
            elif command_type == 'performance':
                data = generate_inline_analysis_data()
                response = {
                    'result': 'inline_performance',
                    'real_data': data,
                    'sql': 'SELECT * FROM inline_performance WHERE date >= "2024-01-01"',
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

@app.get("/api/masking-data-info")
async def get_masking_data_info():
    """마스킹된 데이터 정보 조회"""
    # 마스킹된 엑셀 데이터 로드 시도
    load_masking_data(excel_name='masking_df.xlsx')
    global masking_df
    
    if masking_df is None:
        return {
            "status": "no_data",
            "message": "마스킹된 엑셀 파일이 로드되지 않았습니다",
            "file_exists": os.path.exists('masking_df.xlsx')
        }
    
    if masking_df.empty:
        return {
            "status": "empty_data",
            "message": "마스킹된 데이터가 비어있습니다"
        }
    
    # 데이터 정보 반환
    info = {
        "status": "loaded",
        "message": "마스킹된 데이터가 성공적으로 로드되었습니다",
        "shape": {
            "rows": int(masking_df.shape[0]),
            "columns": int(masking_df.shape[1])
        },
        "columns": list(masking_df.columns),
        "data_types": {col: str(dtype) for col, dtype in masking_df.dtypes.items()},
        "sample_data": masking_df.head(3).to_dict('records') if len(masking_df) > 0 else []
    }
    
    # PARA 컬럼 정보
    if 'PARA' in masking_df.columns:
        para_counts = masking_df['PARA'].value_counts().to_dict()
        info["para_info"] = {
            "unique_paras": list(para_counts.keys()),
            "counts": para_counts
        }
    
    return info

@app.post("/api/reload-masking-data")
async def reload_masking_data():
    """마스킹된 엑셀 데이터 다시 로드"""
    success = load_masking_data(excel_name='masking_df.xlsx')
    
    if success:
        return {
            "status": "success",
            "message": "마스킹된 데이터를 성공적으로 다시 로드했습니다",
            "shape": {
                "rows": int(masking_df.shape[0]),
                "columns": int(masking_df.shape[1])
            } if masking_df is not None else None
        }
    else:
        return {
            "status": "error",
            "message": "마스킹된 데이터 로드에 실패했습니다"
        }

if __name__ == "__main__":
    import uvicorn
    app.mount("/static", StaticFiles(directory="static"), name="static")
    uvicorn.run(app, host="0.0.0.0", port=8000) 
