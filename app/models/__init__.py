"""
Models package - Contains all Pydantic models and schemas
"""

from .chat_models import (
    ChatRoom,
    ChatHistory,
    Message,
    BotResponse,
    ChatRequest,
    EditMessageRequest,
    UpdateChatRoomNameRequest,
    ChatRoomListItem,
    ChatRoomListResponse,
    ChatHistoryResponse,
    ChatRoomDetailResponse
)

from .auth_models import (
    UserInfo,
    SSOLoginRequest,
    SSOLoginResponse,
    TokenVerificationResponse,
    TokenRefreshResponse,
    SessionData,
    JWTPayload
)

__all__ = [
    "ChatRoom",
    "ChatHistory", 
    "Message",
    "BotResponse",
    "ChatRequest",
    "EditMessageRequest",
    "UpdateChatRoomNameRequest",
    "ChatRoomListItem",
    "ChatRoomListResponse",
    "ChatHistoryResponse",
    "ChatRoomDetailResponse",
    "UserInfo",
    "SSOLoginRequest",
    "SSOLoginResponse",
    "TokenVerificationResponse",
    "TokenRefreshResponse",
    "SessionData",
    "JWTPayload"
]
