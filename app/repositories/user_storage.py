"""
User storage repository - Handles user session data persistence with PostgreSQL
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging
import json

from app.models import SessionData
from app.database import db_connection

logger = logging.getLogger(__name__)


class UserStorage:
    """PostgreSQL 기반 유저 스토리지"""
    
    def __init__(self):
        pass
    
    def create_session(self, session_id: str, user_data: dict, source: Optional[str] = None) -> SessionData:
        """새 세션 생성"""
        try:
            user_id = user_data.get("userId")
            if not user_id:
                raise ValueError("user_data must contain userId")
            
            # 만료 시간 설정 (24시간 후)
            expires_at = datetime.now() + timedelta(hours=24)
            
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO service_user_storage (user_id, session_id, user_data, source, expires_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    RETURNING id, user_id, session_id, user_data, source, created_at, expires_at
                """, (user_id, session_id, json.dumps(user_data), source, expires_at))
                
                result = cursor.fetchone()
                session_data = SessionData(
                    sessionId=result['session_id'],
                    user=json.loads(result['user_data']),
                    source=result['source'],
                    createdAt=result['created_at'].isoformat()
                )
                
                logger.info(f"Created session {session_id} for user {user_id}")
                return session_data
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """세션 조회"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT user_id, session_id, user_data, source, created_at, expires_at
                    FROM service_user_storage 
                    WHERE session_id = %s AND is_active = TRUE AND expires_at > CURRENT_TIMESTAMP
                """, (session_id,))
                
                result = cursor.fetchone()
                if result:
                    return SessionData(
                        sessionId=result['session_id'],
                        user=json.loads(result['user_data']),
                        source=result['source'],
                        createdAt=result['created_at'].isoformat()
                    )
                return None
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    def update_session(self, session_id: str, user_data: dict) -> Optional[SessionData]:
        """세션 업데이트"""
        try:
            user_id = user_data.get("userId")
            if not user_id:
                raise ValueError("user_data must contain userId")
            
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE service_user_storage 
                    SET user_data = %s, updated_at = CURRENT_TIMESTAMP, expires_at = %s
                    WHERE session_id = %s AND is_active = TRUE
                    RETURNING user_id, session_id, user_data, source, created_at, expires_at
                """, (json.dumps(user_data), datetime.now() + timedelta(hours=24), session_id))
                
                result = cursor.fetchone()
                if result:
                    session_data = SessionData(
                        sessionId=result['session_id'],
                        user=json.loads(result['user_data']),
                        source=result['source'],
                        createdAt=result['created_at'].isoformat()
                    )
                    logger.info(f"Updated session {session_id}")
                    return session_data
                return None
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """세션 삭제 (soft delete)"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE service_user_storage 
                    SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = %s
                """, (session_id,))
                
                if cursor.rowcount > 0:
                    logger.info(f"Deleted session {session_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """특정 사용자의 모든 활성 세션 조회"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT user_id, session_id, user_data, source, created_at, expires_at
                    FROM service_user_storage 
                    WHERE user_id = %s AND is_active = TRUE AND expires_at > CURRENT_TIMESTAMP
                    ORDER BY created_at DESC
                """, (user_id,))
                
                results = cursor.fetchall()
                sessions = []
                
                for row in results:
                    session_data = SessionData(
                        sessionId=row['session_id'],
                        user=json.loads(row['user_data']),
                        source=row['source'],
                        createdAt=row['created_at'].isoformat()
                    )
                    sessions.append(session_data)
                
                logger.info(f"Retrieved {len(sessions)} active sessions for user {user_id}")
                return sessions
        except Exception as e:
            logger.error(f"Failed to get user sessions for {user_id}: {e}")
            return []
    
    def cleanup_expired_sessions(self, expiration_hours: int = 24) -> int:
        """만료된 세션 정리"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE service_user_storage 
                    SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                    WHERE expires_at <= CURRENT_TIMESTAMP AND is_active = TRUE
                """)
                
                expired_count = cursor.rowcount
                if expired_count > 0:
                    logger.info(f"Cleaned up {expired_count} expired sessions")
                
                return expired_count
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0
    
    def get_session_count(self) -> int:
        """전체 활성 세션 수 반환"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM service_user_storage 
                    WHERE is_active = TRUE AND expires_at > CURRENT_TIMESTAMP
                """)
                
                result = cursor.fetchone()
                return result['count'] if result else 0
        except Exception as e:
            logger.error(f"Failed to get session count: {e}")
            return 0
    
    def extend_session(self, session_id: str, hours: int = 24) -> bool:
        """세션 만료 시간 연장"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE service_user_storage 
                    SET expires_at = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = %s AND is_active = TRUE
                """, (datetime.now() + timedelta(hours=hours), session_id))
                
                if cursor.rowcount > 0:
                    logger.info(f"Extended session {session_id} by {hours} hours")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to extend session {session_id}: {e}")
            return False