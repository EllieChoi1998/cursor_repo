"""
Chat storage repository - Handles all chat data persistence
"""

import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from app.models import (
    ChatRoom, ChatHistory, Message, BotResponse,
    ChatRoomListItem, ChatHistoryResponse
)


class ChatStorage:
    """메모리 기반 저장소 (나중에 SQL로 교체 가능)"""
    
    def __init__(self):
        self.chatrooms: Dict[int, ChatRoom] = {}
        self.messages: Dict[str, Message] = {}
        self.responses: Dict[str, BotResponse] = {}
        self.chat_histories: Dict[int, List[ChatHistory]] = {}  # 채팅 기록 저장
        self.next_chatroom_id = 1
        self.next_chat_id = 1
    
    def create_chatroom(self, user_id: str) -> ChatRoom:
        """새 채팅방 생성 (user_id 파라미터 추가)"""
        chatroom_id = self.next_chatroom_id
        self.next_chatroom_id += 1
        
        chatroom = ChatRoom(
            id=chatroom_id,
            name=f"채팅방 #{chatroom_id}",  # 기본 이름 설정
            user_id=user_id
        )
        self.chatrooms[chatroom_id] = chatroom
        self.chat_histories[chatroom_id] = []  # 빈 히스토리 초기화
        return chatroom
    
    def get_chatroom(self, chatroom_id: int) -> Optional[ChatRoom]:
        """채팅방 조회"""
        return self.chatrooms.get(chatroom_id)
    
    def get_all_chatrooms(self, user_id: str) -> List[ChatRoomListItem]:
        """특정 유저의 모든 채팅방 조회 (API 명세 형식으로)"""
        print(f"🔍 get_all_chatrooms called for user: {user_id}. Chatrooms: {list(self.chatrooms.keys())}")
        result = []
        for chatroom_id, chatroom in self.chatrooms.items():
            # 유저 ID가 일치하는 채팅방만 조회
            if chatroom.user_id != user_id:
                continue
                
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
        print(f"✅ Returning {len(result)} chatrooms for user {user_id}")
        return result
    
    def get_chatroom_history(self, chatroom_id: int, user_id: str) -> Optional[ChatHistoryResponse]:
        """채팅방 히스토리 조회 (유저 권한 확인)"""
        if chatroom_id not in self.chatrooms:
            return None
        
        # 유저 권한 확인
        chatroom = self.chatrooms[chatroom_id]
        if chatroom.user_id != user_id:
            return None
        
        histories = self.chat_histories.get(chatroom_id, [])
        return ChatHistoryResponse(
            chatroom_id=chatroom_id,
            recent_conversations=histories,
            count=len(histories)
        )
    
    def delete_chatroom(self, chatroom_id: int, user_id: str) -> bool:
        """채팅방 삭제 (유저 권한 확인)"""
        if chatroom_id in self.chatrooms:
            # 유저 권한 확인
            chatroom = self.chatrooms[chatroom_id]
            if chatroom.user_id != user_id:
                return False
                
            del self.chatrooms[chatroom_id]
            # 관련 메시지와 응답, 히스토리도 삭제
            self.messages = {k: v for k, v in self.messages.items() if v.chatroom_id != chatroom_id}
            self.responses = {k: v for k, v in self.responses.items() if v.chatroom_id != chatroom_id}
            if chatroom_id in self.chat_histories:
                del self.chat_histories[chatroom_id]
            return True
        return False
    
    def add_message(self, chatroom_id: int, user_id: str, content: str, message_type: str, data_type: str) -> Message:
        """메시지 추가 (user_id 파라미터 추가)"""
        message_id = str(uuid.uuid4())
        message = Message(
            id=message_id,
            chatroom_id=chatroom_id,
            user_id=user_id,
            content=content,
            message_type=message_type,
            timestamp=datetime.now(),
            data_type=data_type
        )
        self.messages[message_id] = message
        return message
    
    def add_chat_history(self, chatroom_id: int, user_id: str, user_message: str, bot_response: str, user_time: datetime = None, response_time: datetime = None) -> ChatHistory:
        """채팅 히스토리 추가 (user_id 파라미터 추가)"""
        chat_id = self.next_chat_id
        self.next_chat_id += 1
        
        print(f"🔧 Creating chat history with chat_id: {chat_id} for chatroom: {chatroom_id}, user: {user_id}")
        
        # 시간 설정: 파라미터로 받은 시간이 있으면 사용, 없으면 현재 시간
        chat_time = user_time if user_time else datetime.now()
        bot_response_time = response_time if response_time else datetime.now()
        
        history = ChatHistory(
            chat_id=chat_id,
            chatroom_id=chatroom_id,
            user_id=user_id,
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
    
    def edit_chat_history(self, chatroom_id: int, chat_id: int, user_id: str, user_message: str, bot_response: str) -> Optional[ChatHistory]:
        """채팅 히스토리 수정 (기존 chat_id 유지, user_id 파라미터 추가)"""
        if chatroom_id not in self.chat_histories:
            print(f"❌ Chatroom {chatroom_id} not found in histories")
            return None
        
        # 기존 히스토리에서 해당 chat_id를 찾아 업데이트
        for history in self.chat_histories[chatroom_id]:
            if history.chat_id == chat_id and history.user_id == user_id:
                print(f"🔧 Updating existing chat history with chat_id: {chat_id}, user: {user_id}")
                
                # 히스토리 내용 업데이트
                history.user_message = user_message
                history.chat_time = datetime.now()
                history.bot_response = bot_response
                history.response_time = datetime.now()
                
                print(f"✅ Updated chat history with chat_id: {chat_id}")
                print(f"📅 Updated time: {history.chat_time}")
                return history
        
        print(f"❌ Chat history with chat_id {chat_id} not found in chatroom {chatroom_id} for user {user_id}")
        return None
    
    def get_messages_by_chatroom(self, chatroom_id: int) -> List[Message]:
        """채팅방의 메시지 조회"""
        return [msg for msg in self.messages.values() if msg.chatroom_id == chatroom_id]
    
    def add_response(self, message_id: str, chatroom_id: int, user_id: str, content: Dict[str, Any]) -> BotResponse:
        """봇 응답 추가 (user_id 파라미터 추가)"""
        response_id = str(uuid.uuid4())
        response = BotResponse(
            id=response_id,
            message_id=message_id,
            chatroom_id=chatroom_id,
            user_id=user_id,
            content=content,
            timestamp=datetime.now()
        )
        self.responses[response_id] = response
        return response
    
    def get_responses_by_chatroom(self, chatroom_id: int) -> List[BotResponse]:
        """채팅방의 응답 조회"""
        return [resp for resp in self.responses.values() if resp.chatroom_id == chatroom_id]

    def update_chatroom_name(self, chatroom_id: int, name: str, user_id: str) -> Optional[ChatRoom]:
        """채팅방 이름 수정 (유저 권한 확인)"""
        if chatroom_id in self.chatrooms:
            # 유저 권한 확인
            chatroom = self.chatrooms[chatroom_id]
            if chatroom.user_id != user_id:
                return None
                
            self.chatrooms[chatroom_id].name = name
            return self.chatrooms[chatroom_id]
        return None
