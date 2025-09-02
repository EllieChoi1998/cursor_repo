"""
JWT utility functions for authentication
"""

import jwt
import datetime
from typing import Dict, Any
from fastapi import HTTPException, status

from app.config import settings


def create_jwt_token(user_data: Dict[str, Any], source: str = None) -> str:
    """JWT 토큰 생성"""
    payload = {
        "userId": user_data["userId"],
        "loginTime": user_data["loginTime"],
        "source": source,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """JWT 토큰 검증 및 페이로드 반환"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 만료되었습니다."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다."
        )


def decode_token_payload(token: str) -> Dict[str, Any]:
    """토큰을 디코드하여 페이로드 반환 (검증 없음)"""
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="토큰 형식이 올바르지 않습니다."
        )


def is_token_expired(token: str) -> bool:
    """토큰이 만료되었는지 확인"""
    try:
        payload = decode_token_payload(token)
        exp = payload.get("exp")
        if exp:
            return datetime.datetime.utcnow().timestamp() > exp
        return True
    except Exception:
        return True


def get_user_id_from_token(token: str) -> str:
    """토큰에서 사용자 ID 추출"""
    try:
        payload = decode_token_payload(token)
        return payload.get("userId", "")
    except Exception:
        return ""


def refresh_token(old_token: str) -> str:
    """기존 토큰을 갱신하여 새 토큰 생성"""
    # 먼저 기존 토큰이 유효한지 확인
    payload = verify_jwt_token(old_token)
    
    # 새로운 토큰 생성
    user_data = {
        "userId": payload["userId"],
        "loginTime": datetime.datetime.now().isoformat()
    }
    
    return create_jwt_token(user_data, payload.get("source"))
