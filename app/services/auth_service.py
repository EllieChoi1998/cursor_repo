"""
Authentication service - Handles SSO and JWT authentication logic
"""

import datetime
from typing import Dict, Any

from app.models import (
    SSOLoginRequest, SSOLoginResponse, TokenVerificationResponse, 
    TokenRefreshResponse, UserInfo
)
from app.repositories import SessionStorage
from app.utils.jwt_utils import create_jwt_token, verify_jwt_token, refresh_token
from app.config import settings


class AuthService:
    """인증 서비스"""
    
    def __init__(self, session_storage: SessionStorage):
        self.session_storage = session_storage
    
    def process_sso_login(self, request: SSOLoginRequest) -> SSOLoginResponse:
        """SSO 로그인 처리"""

        print(f"SSO 로그인 요청 수신: {request}")
        
        # 사용자 정보 유효성 검사
        if not request.userId:
            raise ValueError("사용자 ID가 필요합니다.")
        
        if request.userId != "developer":
            raise ValueError("권한이 없습니다.")
        # JWT 토큰 생성을 위한 사용자 데이터 준비
        user_data = {
            "userId": request.userId,
            "loginTime": datetime.datetime.now().isoformat()
        }
        
        # JWT 토큰 생성
        jwt_token = create_jwt_token(user_data)
        session_id = f"sso_{int(datetime.datetime.now().timestamp())}_{request.userId}"
        
        # 세션 저장
        self.session_storage.create_session(session_id, user_data, None)
        
        print(f"JWT 토큰 생성 완료: sessionId={session_id}, userId={request.userId}")
        
        # 성공 응답 생성
        redirect_url = f"http://192.168.0.196:8080/sso-callback?token={jwt_token}"
        
        return SSOLoginResponse(
            success=True,
            token=jwt_token,
            sessionId=session_id,
            message="SSO 로그인 성공",
            redirectUrl=redirect_url,
            userId=request.userId
        )
    
    def verify_token(self, token: str) -> TokenVerificationResponse:
        """JWT 토큰 검증"""
        payload = verify_jwt_token(token)
        
        return TokenVerificationResponse(
            success=True,
            message="유효한 JWT 토큰입니다.",
            userId=payload["userId"],
            loginTime=payload["loginTime"],
            issuedAt=datetime.datetime.fromtimestamp(payload["iat"]).isoformat(),
            expiresAt=datetime.datetime.fromtimestamp(payload["exp"]).isoformat()
        )
    
    def refresh_user_token(self, token: str) -> TokenRefreshResponse:
        """JWT 토큰 갱신"""
        payload = verify_jwt_token(token)
        
        # 새로운 JWT 토큰 생성
        user_data = {
            "userId": payload["userId"],
            "loginTime": datetime.datetime.now().isoformat()
        }
        new_jwt_token = create_jwt_token(user_data, payload.get("source"))
        
        return TokenRefreshResponse(
            success=True,
            message="토큰이 갱신되었습니다.",
            token=new_jwt_token,
            userId=payload["userId"]
        )
    
    def logout_user(self, session_id: str) -> bool:
        """사용자 로그아웃 (세션 삭제)"""
        return self.session_storage.delete_session(session_id)
    
    def get_user_sessions(self, user_id: str) -> list:
        """사용자의 모든 세션 조회"""
        return self.session_storage.get_user_sessions(user_id)
    
    def cleanup_expired_sessions(self) -> int:
        """만료된 세션 정리"""
        return self.session_storage.cleanup_expired_sessions(settings.JWT_EXPIRATION_HOURS)
    
    def validate_user_permissions(self, token: str, required_role: str = None) -> Dict[str, Any]:
        """사용자 권한 검증"""
        payload = verify_jwt_token(token)
    
        return {
            "userId": payload["userId"],
            "role": "user",  # 기본 역할
            "loginTime": payload["loginTime"]
        }
