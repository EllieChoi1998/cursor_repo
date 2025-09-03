"""
User repository - Handles user data persistence with PostgreSQL
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.database import db_connection

logger = logging.getLogger(__name__)


class UserRepository:
    """PostgreSQL 기반 유저 저장소"""
    
    def __init__(self):
        pass
    
    def create_user(self, user_id: str, username: str, email: str = None, full_name: str = None) -> bool:
        """새 유저 생성"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (user_id, username, email, full_name, updated_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id) DO NOTHING
                """, (user_id, username, email, full_name))
                
                if cursor.rowcount > 0:
                    logger.info(f"Created user {user_id}")
                    return True
                else:
                    logger.info(f"User {user_id} already exists")
                    return False
        except Exception as e:
            logger.error(f"Failed to create user {user_id}: {e}")
            return False
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """유저 조회"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, user_id, username, email, full_name, created_at, updated_at, is_active
                    FROM users 
                    WHERE user_id = %s AND is_active = TRUE
                """, (user_id,))
                
                result = cursor.fetchone()
                if result:
                    return dict(result)
                return None
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None
    
    def update_user(self, user_id: str, username: str = None, email: str = None, full_name: str = None) -> bool:
        """유저 정보 업데이트"""
        try:
            # 업데이트할 필드들만 동적으로 구성
            update_fields = []
            params = []
            
            if username is not None:
                update_fields.append("username = %s")
                params.append(username)
            
            if email is not None:
                update_fields.append("email = %s")
                params.append(email)
            
            if full_name is not None:
                update_fields.append("full_name = %s")
                params.append(full_name)
            
            if not update_fields:
                return True  # 업데이트할 필드가 없음
            
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            params.append(user_id)
            
            with db_connection.get_cursor() as cursor:
                cursor.execute(f"""
                    UPDATE users 
                    SET {', '.join(update_fields)}
                    WHERE user_id = %s AND is_active = TRUE
                """, params)
                
                if cursor.rowcount > 0:
                    logger.info(f"Updated user {user_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            return False
    
    def deactivate_user(self, user_id: str) -> bool:
        """유저 비활성화 (soft delete)"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE users 
                    SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, (user_id,))
                
                if cursor.rowcount > 0:
                    logger.info(f"Deactivated user {user_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to deactivate user {user_id}: {e}")
            return False
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """모든 활성 유저 조회"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, user_id, username, email, full_name, created_at, updated_at, is_active
                    FROM users 
                    WHERE is_active = TRUE
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                
                results = cursor.fetchall()
                users = [dict(row) for row in results]
                
                logger.info(f"Retrieved {len(users)} users")
                return users
        except Exception as e:
            logger.error(f"Failed to get all users: {e}")
            return []
    
    def get_user_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """유저 통계 조회"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        u.user_id,
                        u.username,
                        COUNT(DISTINCT c.id) as total_chatrooms,
                        COUNT(DISTINCT CASE WHEN c.is_deleted = FALSE THEN c.id END) as active_chatrooms,
                        COUNT(DISTINCT ch.id) as total_messages,
                        MAX(ch.response_time) as last_activity
                    FROM users u
                    LEFT JOIN chatrooms c ON u.user_id = c.user_id
                    LEFT JOIN chat_histories ch ON c.id = ch.chatroom_id
                    WHERE u.user_id = %s AND u.is_active = TRUE
                    GROUP BY u.user_id, u.username
                """, (user_id,))
                
                result = cursor.fetchone()
                if result:
                    return dict(result)
                return None
        except Exception as e:
            logger.error(f"Failed to get user stats for {user_id}: {e}")
            return None
    
    def search_users(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """유저 검색"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, user_id, username, email, full_name, created_at, updated_at, is_active
                    FROM users 
                    WHERE is_active = TRUE 
                    AND (username ILIKE %s OR email ILIKE %s OR full_name ILIKE %s)
                    ORDER BY username
                    LIMIT %s
                """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))
                
                results = cursor.fetchall()
                users = [dict(row) for row in results]
                
                logger.info(f"Found {len(users)} users matching '{query}'")
                return users
        except Exception as e:
            logger.error(f"Failed to search users: {e}")
            return []