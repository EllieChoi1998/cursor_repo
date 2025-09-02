"""
Session storage repository - Handles session data persistence
"""

from typing import Dict, Optional
from datetime import datetime

from app.models import SessionData


class SessionStorage:
    """세션 저장소 (실제로는 Redis나 DB 사용 권장)"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionData] = {}
    
    def create_session(self, session_id: str, user_data: dict, source: Optional[str] = None) -> SessionData:
        """새 세션 생성"""
        session_data = SessionData(
            sessionId=session_id,
            user=user_data,
            source=source,
            createdAt=datetime.now().isoformat()
        )
        
        self.sessions[session_id] = session_data
        print(f"Session created: {session_id}")
        return session_data
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """세션 조회"""
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, user_data: dict) -> Optional[SessionData]:
        """세션 업데이트"""
        if session_id in self.sessions:
            self.sessions[session_id].user = user_data
            return self.sessions[session_id]
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            print(f"Session deleted: {session_id}")
            return True
        return False
    
    def get_user_sessions(self, user_id: str) -> list[SessionData]:
        """특정 사용자의 모든 세션 조회"""
        user_sessions = []
        for session in self.sessions.values():
            if session.user.get("userId") == user_id:
                user_sessions.append(session)
        return user_sessions
    
    def cleanup_expired_sessions(self, expiration_hours: int = 24):
        """만료된 세션 정리"""
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=expiration_hours)
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            session_time = datetime.fromisoformat(session.createdAt)
            if session_time < cutoff_time:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            print(f"Expired session removed: {session_id}")
        
        return len(expired_sessions)
    
    def get_session_count(self) -> int:
        """전체 세션 수 반환"""
        return len(self.sessions)
