"""
Authentication-related Pydantic models and schemas
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserInfo(BaseModel):
    """사용자 정보 모델"""
    userId: str
    userName: str
    email: str
    role: str
    loginTime: Optional[str] = None
    sourceIp: Optional[str] = None


class SSOLoginRequest(BaseModel):
    """SSO 로그인 요청 모델"""
    userId: str


class SSOLoginResponse(BaseModel):
    """SSO 로그인 응답 모델"""
    success: bool
    token: str
    sessionId: str
    message: str
    redirectUrl: str
    userId: str


class TokenVerificationResponse(BaseModel):
    """토큰 검증 응답 모델"""
    success: bool
    message: str
    userId: str
    loginTime: str
    issuedAt: str
    expiresAt: str


class TokenRefreshResponse(BaseModel):
    """토큰 갱신 응답 모델"""
    success: bool
    message: str
    token: str
    userId: str


class SessionData(BaseModel):
    """세션 데이터 모델"""
    sessionId: str
    user: dict
    source: Optional[str] = None
    createdAt: str


class JWTPayload(BaseModel):
    """JWT 페이로드 모델"""
    userId: str
    loginTime: str
    iat: int
    exp: int
