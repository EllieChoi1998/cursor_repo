"""
Data preservation utilities - Ensures data integrity when chatrooms are deleted
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.database import db_connection

logger = logging.getLogger(__name__)


class DataPreservation:
    """데이터 보존 관련 유틸리티"""
    
    def __init__(self):
        pass
    
    def get_chatroom_data_summary(self, chatroom_id: int) -> Optional[Dict[str, Any]]:
        """채팅방 삭제 전 데이터 요약 조회"""
        try:
            with db_connection.get_cursor() as cursor:
                # 채팅방 기본 정보
                cursor.execute("""
                    SELECT id, name, user_id, created_at, updated_at, is_deleted, deleted_at
                    FROM chatrooms 
                    WHERE id = %s
                """, (chatroom_id,))
                
                chatroom_info = cursor.fetchone()
                if not chatroom_info:
                    return None
                
                # 메시지 수
                cursor.execute("""
                    SELECT COUNT(*) as message_count
                    FROM messages 
                    WHERE chatroom_id = %s
                """, (chatroom_id,))
                
                message_count = cursor.fetchone()['message_count']
                
                # 봇 응답 수
                cursor.execute("""
                    SELECT COUNT(*) as response_count
                    FROM bot_responses 
                    WHERE chatroom_id = %s
                """, (chatroom_id,))
                
                response_count = cursor.fetchone()['response_count']
                
                # 채팅 히스토리 수
                cursor.execute("""
                    SELECT COUNT(*) as history_count
                    FROM chat_histories 
                    WHERE chatroom_id = %s
                """, (chatroom_id,))
                
                history_count = cursor.fetchone()['history_count']
                
                # 최근 활동 시간
                cursor.execute("""
                    SELECT MAX(response_time) as last_activity
                    FROM chat_histories 
                    WHERE chatroom_id = %s
                """, (chatroom_id,))
                
                last_activity = cursor.fetchone()['last_activity']
                
                return {
                    'chatroom_info': dict(chatroom_info),
                    'message_count': message_count,
                    'response_count': response_count,
                    'history_count': history_count,
                    'last_activity': last_activity,
                    'total_data_points': message_count + response_count + history_count
                }
        except Exception as e:
            logger.error(f"Failed to get chatroom data summary for {chatroom_id}: {e}")
            return None
    
    def get_deleted_chatrooms_data(self, user_id: str) -> List[Dict[str, Any]]:
        """삭제된 채팅방의 데이터 조회 (복구 가능한 데이터)"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        c.id,
                        c.name,
                        c.user_id,
                        c.created_at,
                        c.deleted_at,
                        COUNT(DISTINCT m.id) as message_count,
                        COUNT(DISTINCT br.id) as response_count,
                        COUNT(DISTINCT ch.chat_id) as history_count
                    FROM chatrooms c
                    LEFT JOIN messages m ON c.id = m.chatroom_id
                    LEFT JOIN bot_responses br ON c.id = br.chatroom_id
                    LEFT JOIN chat_histories ch ON c.id = ch.chatroom_id
                    WHERE c.user_id = %s AND c.is_deleted = TRUE
                    GROUP BY c.id, c.name, c.user_id, c.created_at, c.deleted_at
                    ORDER BY c.deleted_at DESC
                """, (user_id,))
                
                results = cursor.fetchall()
                deleted_chatrooms = []
                
                for row in results:
                    chatroom_data = {
                        'id': row['id'],
                        'name': row['name'],
                        'user_id': row['user_id'],
                        'created_at': row['created_at'],
                        'deleted_at': row['deleted_at'],
                        'message_count': row['message_count'],
                        'response_count': row['response_count'],
                        'history_count': row['history_count'],
                        'total_data_points': row['message_count'] + row['response_count'] + row['history_count']
                    }
                    deleted_chatrooms.append(chatroom_data)
                
                logger.info(f"Retrieved {len(deleted_chatrooms)} deleted chatrooms for user {user_id}")
                return deleted_chatrooms
        except Exception as e:
            logger.error(f"Failed to get deleted chatrooms data for user {user_id}: {e}")
            return []
    
    def restore_chatroom(self, chatroom_id: int, user_id: str) -> bool:
        """삭제된 채팅방 복구"""
        try:
            with db_connection.get_cursor() as cursor:
                # 유저 권한 확인
                cursor.execute("""
                    SELECT user_id FROM chatrooms WHERE id = %s
                """, (chatroom_id,))
                
                result = cursor.fetchone()
                if not result or result['user_id'] != user_id:
                    logger.warning(f"User {user_id} not authorized to restore chatroom {chatroom_id}")
                    return False
                
                # 채팅방 복구
                cursor.execute("""
                    UPDATE chatrooms 
                    SET is_deleted = FALSE, deleted_at = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (chatroom_id,))
                
                if cursor.rowcount > 0:
                    logger.info(f"Restored chatroom {chatroom_id} for user {user_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to restore chatroom {chatroom_id}: {e}")
            return False
    
    def permanently_delete_chatroom_data(self, chatroom_id: int, user_id: str) -> bool:
        """채팅방과 관련된 모든 데이터를 영구 삭제 (주의: 복구 불가능)"""
        try:
            with db_connection.get_cursor() as cursor:
                # 유저 권한 확인
                cursor.execute("""
                    SELECT user_id FROM chatrooms WHERE id = %s
                """, (chatroom_id,))
                
                result = cursor.fetchone()
                if not result or result['user_id'] != user_id:
                    logger.warning(f"User {user_id} not authorized to permanently delete chatroom {chatroom_id}")
                    return False
                
                # 관련 데이터 삭제 (외래키 제약조건에 의해 순서 중요)
                cursor.execute("DELETE FROM bot_responses WHERE chatroom_id = %s", (chatroom_id,))
                cursor.execute("DELETE FROM messages WHERE chatroom_id = %s", (chatroom_id,))
                cursor.execute("DELETE FROM chat_histories WHERE chatroom_id = %s", (chatroom_id,))
                cursor.execute("DELETE FROM chatrooms WHERE id = %s", (chatroom_id,))
                
                logger.warning(f"Permanently deleted all data for chatroom {chatroom_id} by user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to permanently delete chatroom data {chatroom_id}: {e}")
            return False
    
    def get_user_data_statistics(self, user_id: str) -> Dict[str, Any]:
        """유저의 전체 데이터 통계"""
        try:
            with db_connection.get_cursor() as cursor:
                # 활성 채팅방 수
                cursor.execute("""
                    SELECT COUNT(*) as active_chatrooms
                    FROM chatrooms 
                    WHERE user_id = %s AND is_deleted = FALSE
                """, (user_id,))
                
                active_chatrooms = cursor.fetchone()['active_chatrooms']
                
                # 삭제된 채팅방 수
                cursor.execute("""
                    SELECT COUNT(*) as deleted_chatrooms
                    FROM chatrooms 
                    WHERE user_id = %s AND is_deleted = TRUE
                """, (user_id,))
                
                deleted_chatrooms = cursor.fetchone()['deleted_chatrooms']
                
                # 총 메시지 수
                cursor.execute("""
                    SELECT COUNT(*) as total_messages
                    FROM messages m
                    JOIN chatrooms c ON m.chatroom_id = c.id
                    WHERE c.user_id = %s
                """, (user_id,))
                
                total_messages = cursor.fetchone()['total_messages']
                
                # 총 채팅 히스토리 수
                cursor.execute("""
                    SELECT COUNT(*) as total_histories
                    FROM chat_histories ch
                    JOIN chatrooms c ON ch.chatroom_id = c.id
                    WHERE c.user_id = %s
                """, (user_id,))
                
                total_histories = cursor.fetchone()['total_histories']
                
                # 최근 활동 시간
                cursor.execute("""
                    SELECT MAX(ch.response_time) as last_activity
                    FROM chat_histories ch
                    JOIN chatrooms c ON ch.chatroom_id = c.id
                    WHERE c.user_id = %s
                """, (user_id,))
                
                last_activity = cursor.fetchone()['last_activity']
                
                return {
                    'user_id': user_id,
                    'active_chatrooms': active_chatrooms,
                    'deleted_chatrooms': deleted_chatrooms,
                    'total_messages': total_messages,
                    'total_histories': total_histories,
                    'last_activity': last_activity,
                    'total_data_points': total_messages + total_histories
                }
        except Exception as e:
            logger.error(f"Failed to get user data statistics for {user_id}: {e}")
            return {}
    
    def cleanup_old_deleted_data(self, days_old: int = 30) -> int:
        """오래된 삭제된 데이터 정리 (관리자 기능)"""
        try:
            with db_connection.get_cursor() as cursor:
                # 삭제된 지 오래된 채팅방의 데이터 영구 삭제
                cursor.execute("""
                    DELETE FROM bot_responses 
                    WHERE chatroom_id IN (
                        SELECT id FROM chatrooms 
                        WHERE is_deleted = TRUE 
                        AND deleted_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                    )
                """, (days_old,))
                
                cursor.execute("""
                    DELETE FROM messages 
                    WHERE chatroom_id IN (
                        SELECT id FROM chatrooms 
                        WHERE is_deleted = TRUE 
                        AND deleted_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                    )
                """, (days_old,))
                
                cursor.execute("""
                    DELETE FROM chat_histories 
                    WHERE chatroom_id IN (
                        SELECT id FROM chatrooms 
                        WHERE is_deleted = TRUE 
                        AND deleted_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                    )
                """, (days_old,))
                
                cursor.execute("""
                    DELETE FROM chatrooms 
                    WHERE is_deleted = TRUE 
                    AND deleted_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                """, (days_old,))
                
                cleaned_count = cursor.rowcount
                logger.info(f"Cleaned up {cleaned_count} old deleted chatrooms and their data")
                return cleaned_count
        except Exception as e:
            logger.error(f"Failed to cleanup old deleted data: {e}")
            return 0