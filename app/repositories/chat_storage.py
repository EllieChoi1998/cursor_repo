"""
Chat storage repository - Handles all chat data persistence with PostgreSQL
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from app.models import (
    ChatRoom, ChatHistory, Message, BotResponse,
    ChatRoomListItem, ChatHistoryResponse
)
from app.database import db_connection

logger = logging.getLogger(__name__)


class ChatStorage:
    """PostgreSQL 기반 채팅 저장소"""
    
    def __init__(self):
        pass
    
    def create_chatroom(self, user_id: str) -> ChatRoom:
        """새 채팅방 생성"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO service_chatrooms (name, user_id, updated_at) 
                    VALUES (%s, %s, CURRENT_TIMESTAMP) 
                    RETURNING id, name, user_id, created_at, updated_at
                """, (f"채팅방 #{datetime.now().strftime('%Y%m%d_%H%M%S')}", user_id))
                
                result = cursor.fetchone()
                chatroom = ChatRoom(
                    id=result['id'],
                    name=result['name'],
                    user_id=result['user_id']
                )
                logger.info(f"Created chatroom {chatroom.id} for user {user_id}")
                return chatroom
        except Exception as e:
            logger.error(f"Failed to create chatroom: {e}")
            raise
    
    def get_chatroom(self, chatroom_id: int) -> Optional[ChatRoom]:
        """채팅방 조회"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, user_id, created_at, updated_at 
                    FROM service_chatrooms 
                    WHERE id = %s AND is_deleted = FALSE
                """, (chatroom_id,))
                
                result = cursor.fetchone()
                if result:
                    return ChatRoom(
                        id=result['id'],
                        name=result['name'],
                        user_id=result['user_id']
                    )
                return None
        except Exception as e:
            logger.error(f"Failed to get chatroom {chatroom_id}: {e}")
            return None
    
    def get_all_chatrooms(self, user_id: str) -> List[ChatRoomListItem]:
        """특정 유저의 모든 채팅방 조회"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        c.id,
                        c.name,
                        c.created_at,
                        c.updated_at,
                        COUNT(ch.id) as message_count,
                        COALESCE(MAX(ch.response_time), c.updated_at) as last_activity
                    FROM service_chatrooms c
                    LEFT JOIN service_chat_histories ch ON c.id = ch.chatroom_id
                    WHERE c.user_id = %s AND c.is_deleted = FALSE
                    GROUP BY c.id, c.name, c.created_at, c.updated_at
                    ORDER BY last_activity DESC
                """, (user_id,))
                
                results = cursor.fetchall()
                chatrooms = []
                
                for row in results:
                    item = ChatRoomListItem(
                        id=row['id'],
                        name=row['name'],
                        message_count=row['message_count'],
                        last_activity=row['last_activity']
                    )
                    chatrooms.append(item)
                
                logger.info(f"Retrieved {len(chatrooms)} chatrooms for user {user_id}")
                return chatrooms
        except Exception as e:
            logger.error(f"Failed to get chatrooms for user {user_id}: {e}")
            return []
    
    def get_chatroom_history(self, chatroom_id: int, user_id: str) -> Optional[ChatHistoryResponse]:
        """채팅방 히스토리 조회 (유저 권한 확인)"""
        try:
            with db_connection.get_cursor() as cursor:
                # 유저 권한 확인
                cursor.execute("""
                    SELECT user_id FROM service_chatrooms WHERE id = %s AND is_deleted = FALSE
                """, (chatroom_id,))
                
                result = cursor.fetchone()
                if not result or result['user_id'] != user_id:
                    return None
                
                # 채팅 히스토리 조회
                cursor.execute("""
                    SELECT id, chatroom_id, user_id, user_message, 
                           bot_response, chat_time, response_time
                    FROM service_chat_histories 
                    WHERE chatroom_id = %s 
                    ORDER BY response_time DESC
                """, (chatroom_id,))
                
                results = cursor.fetchall()
                histories = []
                
                for row in results:
                    history = ChatHistory(
                        chat_id=row['id'],  # id를 chat_id로 매핑
                        chatroom_id=row['chatroom_id'],
                        user_id=row['user_id'],
                        user_message=row['user_message'],
                        chat_time=row['chat_time'],
                        bot_response=row['bot_response'],
                        response_time=row['response_time']
                    )
                    histories.append(history)
                
                return ChatHistoryResponse(
                    chatroom_id=chatroom_id,
                    recent_conversations=histories,
                    count=len(histories)
                )
        except Exception as e:
            logger.error(f"Failed to get chatroom history {chatroom_id}: {e}")
            return None
    
    def delete_chatroom(self, chatroom_id: int, user_id: str) -> bool:
        """채팅방 삭제 (soft delete - 연관 데이터 보존)"""
        try:
            with db_connection.get_cursor() as cursor:
                # 유저 권한 확인
                cursor.execute("""
                    SELECT user_id FROM service_chatrooms WHERE id = %s AND is_deleted = FALSE
                """, (chatroom_id,))
                
                result = cursor.fetchone()
                if not result or result['user_id'] != user_id:
                    return False
                
                # Soft delete - 채팅방만 삭제 표시, 연관 데이터는 보존
                cursor.execute("""
                    UPDATE service_chatrooms 
                    SET is_deleted = TRUE, deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (chatroom_id,))
                
                logger.info(f"Soft deleted chatroom {chatroom_id} for user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete chatroom {chatroom_id}: {e}")
            return False
    
    def add_message(self, chatroom_id: int, user_id: str, content: str, message_type: str, data_type: str) -> Message:
        """메시지 추가"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO service_messages (chatroom_id, user_id, content, message_type, data_type, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, chatroom_id, user_id, content, message_type, data_type, timestamp
                """, (chatroom_id, user_id, content, message_type, data_type, datetime.now()))
                
                result = cursor.fetchone()
                message = Message(
                    id=str(result['id']),  # 정수 ID를 문자열로 변환
                    chatroom_id=result['chatroom_id'],
                    user_id=result['user_id'],
                    content=result['content'],
                    message_type=result['message_type'],
                    timestamp=result['timestamp'],
                    data_type=result['data_type']
                )
                logger.info(f"Added message {result['id']} to chatroom {chatroom_id}")
                return message
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            raise
    
    def add_chat_history(self, chatroom_id: int, user_id: str, user_message: str, bot_response: str, user_time: datetime = None, response_time: datetime = None) -> ChatHistory:
        """채팅 히스토리 추가"""
        try:
            # 시간 설정: 파라미터로 받은 시간이 있으면 사용, 없으면 현재 시간
            chat_time = user_time if user_time else datetime.now()
            bot_response_time = response_time if response_time else datetime.now()
            
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO service_chat_histories (chatroom_id, user_id, user_message, bot_response, chat_time, response_time)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, chatroom_id, user_id, user_message, bot_response, chat_time, response_time
                """, (chatroom_id, user_id, user_message, bot_response, chat_time, bot_response_time))
                
                result = cursor.fetchone()
                history = ChatHistory(
                    chat_id=result['id'],  # id를 chat_id로 매핑
                    chatroom_id=result['chatroom_id'],
                    user_id=result['user_id'],
                    user_message=result['user_message'],
                    chat_time=result['chat_time'],
                    bot_response=result['bot_response'],
                    response_time=result['response_time']
                )
                
                logger.info(f"Added chat history {history.chat_id} to chatroom {chatroom_id}")
                return history
        except Exception as e:
            logger.error(f"Failed to add chat history: {e}")
            raise
    
    def edit_chat_history(self, chatroom_id: int, chat_id: int, user_id: str, user_message: str, bot_response: str) -> Optional[ChatHistory]:
        """채팅 히스토리 수정"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE service_chat_histories 
                    SET user_message = %s, bot_response = %s, 
                        chat_time = CURRENT_TIMESTAMP, response_time = CURRENT_TIMESTAMP
                    WHERE id = %s AND chatroom_id = %s AND user_id = %s
                    RETURNING id, chatroom_id, user_id, user_message, bot_response, chat_time, response_time
                """, (user_message, bot_response, chat_id, chatroom_id, user_id))
                
                result = cursor.fetchone()
                if result:
                    history = ChatHistory(
                        chat_id=result['id'],  # id를 chat_id로 매핑
                        chatroom_id=result['chatroom_id'],
                        user_id=result['user_id'],
                        user_message=result['user_message'],
                        chat_time=result['chat_time'],
                        bot_response=result['bot_response'],
                        response_time=result['response_time']
                    )
                    logger.info(f"Updated chat history {chat_id} in chatroom {chatroom_id}")
                    return history
                else:
                    logger.warning(f"Chat history {chat_id} not found in chatroom {chatroom_id} for user {user_id}")
                    return None
        except Exception as e:
            logger.error(f"Failed to edit chat history: {e}")
            return None
    
    def get_messages_by_chatroom(self, chatroom_id: int) -> List[Message]:
        """채팅방의 메시지 조회"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, chatroom_id, user_id, content, message_type, data_type, timestamp
                    FROM service_messages 
                    WHERE chatroom_id = %s 
                    ORDER BY timestamp ASC
                """, (chatroom_id,))
                
                results = cursor.fetchall()
                messages = []
                
                for row in results:
                    message = Message(
                        id=str(row['id']),  # 정수 ID를 문자열로 변환
                        chatroom_id=row['chatroom_id'],
                        user_id=row['user_id'],
                        content=row['content'],
                        message_type=row['message_type'],
                        timestamp=row['timestamp'],
                        data_type=row['data_type']
                    )
                    messages.append(message)
                
                return messages
        except Exception as e:
            logger.error(f"Failed to get messages for chatroom {chatroom_id}: {e}")
            return []
    
    def add_response(self, message_id: str, chatroom_id: int, user_id: str, content: Dict[str, Any]) -> BotResponse:
        """봇 응답 추가"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO service_bot_responses (message_id, chatroom_id, user_id, content, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, message_id, chatroom_id, user_id, content, timestamp
                """, (int(message_id), chatroom_id, user_id, json.dumps(content), datetime.now()))
                
                result = cursor.fetchone()
                response = BotResponse(
                    id=str(result['id']),  # 정수 ID를 문자열로 변환
                    message_id=str(result['message_id']),
                    chatroom_id=result['chatroom_id'],
                    user_id=result['user_id'],
                    content=json.loads(result['content']),
                    timestamp=result['timestamp']
                )
                logger.info(f"Added bot response {result['id']} to chatroom {chatroom_id}")
                return response
        except Exception as e:
            logger.error(f"Failed to add bot response: {e}")
            raise
    
    def get_responses_by_chatroom(self, chatroom_id: int) -> List[BotResponse]:
        """채팅방의 응답 조회"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, message_id, chatroom_id, user_id, content, timestamp
                    FROM service_bot_responses 
                    WHERE chatroom_id = %s 
                    ORDER BY timestamp ASC
                """, (chatroom_id,))
                
                results = cursor.fetchall()
                responses = []
                
                for row in results:
                    response = BotResponse(
                        id=str(row['id']),  # 정수 ID를 문자열로 변환
                        message_id=str(row['message_id']),
                        chatroom_id=row['chatroom_id'],
                        user_id=row['user_id'],
                        content=json.loads(row['content']),
                        timestamp=row['timestamp']
                    )
                    responses.append(response)
                
                return responses
        except Exception as e:
            logger.error(f"Failed to get responses for chatroom {chatroom_id}: {e}")
            return []

    def update_chatroom_name(self, chatroom_id: int, name: str, user_id: str) -> Optional[ChatRoom]:
        """채팅방 이름 수정 (유저 권한 확인)"""
        try:
            with db_connection.get_cursor() as cursor:
                # 유저 권한 확인
                cursor.execute("""
                    SELECT user_id FROM service_chatrooms WHERE id = %s AND is_deleted = FALSE
                """, (chatroom_id,))
                
                result = cursor.fetchone()
                if not result or result['user_id'] != user_id:
                    return None
                
                # 채팅방 이름 업데이트
                cursor.execute("""
                    UPDATE service_chatrooms 
                    SET name = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                    RETURNING id, name, user_id, created_at, updated_at
                """, (name, chatroom_id))
                
                result = cursor.fetchone()
                if result:
                    chatroom = ChatRoom(
                        id=result['id'],
                        name=result['name'],
                        user_id=result['user_id']
                    )
                    logger.info(f"Updated chatroom {chatroom_id} name to {name}")
                    return chatroom
                return None
        except Exception as e:
            logger.error(f"Failed to update chatroom name: {e}")
            return None
