"""
Chat-related Pydantic models and schemas
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List


# 채팅방 모델
class ChatRoom(BaseModel):
    id: int  # 정수로 변경
    name: str  # 채팅방 이름 추가
    user_id: str  # 유저 ID 추가


# 채팅 기록 모델 (새로 추가)
class ChatHistory(BaseModel):
    chat_id: int
    chatroom_id: int
    user_id: str  # 유저 ID 추가
    user_message: str
    chat_time: datetime
    bot_response: str
    response_time: datetime


# 메시지 모델
class Message(BaseModel):
    id: str
    chatroom_id: int  # 정수로 변경
    user_id: str  # 유저 ID 추가
    content: str
    message_type: str  # 'user', 'bot'
    timestamp: datetime
    data_type: str  # 'pcm', 'inline', 'rag'


# 응답 모델
class BotResponse(BaseModel):
    id: str
    message_id: str  # 연결된 사용자 메시지 ID
    chatroom_id: int  # 정수로 변경
    user_id: str  # 유저 ID 추가
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
