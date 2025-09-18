"""
Authentication router - Handles SSO and JWT authentication endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import datetime
from typing import Optional

from app.models import SSOLoginRequest
from app.services import AuthService
from app.repositories import UserStorage

router = APIRouter()

# HTTP Bearer 토큰 검증용
security = HTTPBearer()

# Global storage instances - will be set by main app
user_storage = None
auth_service = None


def set_auth_dependencies(storage: UserStorage):
    """Set dependencies for the auth router"""
    global user_storage, auth_service
    user_storage = storage
    auth_service = AuthService(storage)


@router.get("/api/sso-login")
async def sso_login(
    user_id: str = Query(..., description="사용자 ID"),
    user_name: Optional[str] = Query(None, description="사용자 이름"),
    email: Optional[str] = Query(None, description="이메일 주소"),
    role: Optional[str] = Query(None, description="사용자 권한"),
    source_ip: Optional[str] = Query(None, description="소스 IP 주소")
):
    """
    SSO 로그인 API
    192.168.0.200에서 사용자 정보와 함께 호출되는 엔드포인트
    
    Parameters:
    - user_id: 필수 사용자 ID
    - user_name: 선택적 사용자 이름
    - email: 선택적 이메일 주소
    - role: 선택적 사용자 권한
    - source_ip: 선택적 소스 IP 주소
    """
    print(f"SSO 로그인 API 호출: user_id={user_id}, user_name={user_name}, email={email}, role={role}, source_ip={source_ip}")
    try:
        # SSOLoginRequest 객체 생성 (Optional 필드들 포함)
        request = SSOLoginRequest(
            userId=user_id,
            userName=user_name,
            email=email,
            role=role,
            sourceIp=source_ip
        )
        result = auth_service.process_sso_login(request)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"SSO 로그인 처리 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"서버 오류가 발생했습니다: {str(e)}"
        )

@router.get("/api/verify-token/{token}")
async def verify_token(token: str):
    """JWT 토큰 검증 API"""
    try:
        result = auth_service.verify_token(token)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"토큰 검증 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/api/verify-bearer-token")
async def verify_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Bearer 토큰으로 JWT 검증 API"""
    try:
        token = credentials.credentials
        result = auth_service.verify_token(token)
        
        return {
            "success": result.success,
            "message": "유효한 JWT Bearer 토큰입니다.",
            "userId": result.userId,
            "loginTime": result.loginTime,
            "issuedAt": result.issuedAt,
            "expiresAt": result.expiresAt
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bearer 토큰 검증 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/api/refresh-token")
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """JWT 토큰 갱신 API"""
    try:
        token = credentials.credentials
        result = auth_service.refresh_user_token(token)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"토큰 갱신 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/api/logout/{session_id}")
async def logout(session_id: str):
    """로그아웃 API"""
    try:
        success = auth_service.logout_user(session_id)
        if success:
            return {
                "success": True,
                "message": "성공적으로 로그아웃되었습니다.",
                "sessionId": session_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없습니다."
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로그아웃 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/api/user-sessions/{user_id}")
async def get_user_sessions(user_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """사용자 세션 목록 조회 API"""
    try:
        # 토큰 검증 후 권한 확인
        token = credentials.credentials
        user_info = auth_service.validate_user_permissions(token)
        
        # 자신의 세션만 조회 가능 (또는 관리자 권한 확인)
        if user_info["userId"] != user_id and user_info["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="다른 사용자의 세션을 조회할 권한이 없습니다."
            )
        
        sessions = auth_service.get_user_sessions(user_id)
        return {
            "success": True,
            "userId": user_id,
            "sessions": [session.dict() for session in sessions],
            "count": len(sessions)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/api/cleanup-sessions")
async def cleanup_expired_sessions(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """만료된 세션 정리 API (관리자용)"""
    try:
        # 토큰 검증 후 관리자 권한 확인
        token = credentials.credentials
        user_info = auth_service.validate_user_permissions(token, required_role="admin")
        
        cleaned_count = auth_service.cleanup_expired_sessions()
        return {
            "success": True,
            "message": f"{cleaned_count}개의 만료된 세션이 정리되었습니다.",
            "cleanedCount": cleaned_count,
            "requestedBy": user_info["userId"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 정리 중 오류가 발생했습니다: {str(e)}"
        )
