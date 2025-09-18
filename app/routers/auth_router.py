"""
Authentication router - Handles SSO and JWT authentication endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse, HTMLResponse
import datetime
import requests

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


@router.get("/")
async def root():
    """루트페이지 - SSO 로그인 버튼"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SSO 로그인</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 100px auto;
                padding: 20px;
                background-color: #f5f5f5;
                text-align: center;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .sso-button {
                background: linear-gradient(45deg, #007bff, #0056b3);
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 18px;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s ease;
                margin: 20px 0;
                text-decoration: none;
                display: inline-block;
            }
            .sso-button:hover {
                background: linear-gradient(45deg, #0056b3, #004085);
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0,123,255,0.3);
            }
            .info {
                background: #e7f3ff;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
                color: #0066cc;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 SSO 로그인</h1>
            <div class="info">
                <p><strong>서버에서 직접 리다이렉트 처리</strong></p>
                <p>토큰을 사용하지 않고 바로 대시보드로 이동합니다</p>
            </div>
            
            <a href="/sso-redirect?user_id=user123" class="sso-button">
                🔐 SSO 로그인하기
            </a>
            
            <p style="color: #666; margin-top: 30px;">
                사용자 ID: user123 (기본값)
            </p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/sso-redirect")
async def sso_redirect(user_id: str = "user123"):
    """
    SSO 로그인 후 서버에서 직접 리다이렉트 처리
    토큰을 사용하지 않고 바로 대시보드로 이동
    """
    try:
        print(f"SSO 리다이렉트 요청: user_id={user_id}")
        
        # SSO 서버에 로그인 요청 (내부 API 호출)
        sso_request = SSOLoginRequest(userId=user_id)
        sso_result = auth_service.process_sso_login(sso_request)
        
        if sso_result.success:
            print(f"SSO 로그인 성공: {sso_result.userId}")
            # 토큰을 사용하지 않고 바로 대시보드로 리다이렉트
            return RedirectResponse(url="/dashboard")
        else:
            print("SSO 로그인 실패")
            return RedirectResponse(url="/login-failed")
            
    except Exception as e:
        print(f"SSO 리다이렉트 오류: {e}")
        return RedirectResponse(url="/login-failed")


@router.get("/dashboard")
async def dashboard():
    """대시보드 페이지"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>대시보드</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f0f8ff;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: center;
            }
            .success {
                color: #28a745;
                font-size: 24px;
                margin: 20px 0;
            }
            .back-button {
                background: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success">✅ 로그인 성공!</div>
            <h2>대시보드에 오신 것을 환영합니다</h2>
            <p>서버에서 직접 리다이렉트 처리되었습니다.</p>
            <p>토큰 검증 없이 바로 페이지 이동이 완료되었습니다.</p>
            <a href="/" class="back-button">← 홈으로 돌아가기</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/login-failed")
async def login_failed():
    """로그인 실패 페이지"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>로그인 실패</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 100px auto;
                padding: 20px;
                background-color: #fff5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: center;
            }
            .error {
                color: #dc3545;
                font-size: 24px;
                margin: 20px 0;
            }
            .back-button {
                background: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="error">❌ 로그인 실패</div>
            <h2>로그인에 실패했습니다</h2>
            <p>다시 시도해주세요.</p>
            <a href="/" class="back-button">← 다시 로그인하기</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.post("/api/sso-login")
async def sso_login(request: SSOLoginRequest):
    """
    SSO 로그인 API
    192.168.0.200에서 사용자 정보와 함께 호출되는 엔드포인트
    """
    print(f"SSO 로그인 API 호출: {request}")
    try:
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
