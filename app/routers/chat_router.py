"""
Chat router - Handles all chat-related API endpoints
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime

from app.models import (
    ChatRequest, EditMessageRequest, UpdateChatRoomNameRequest
)
from app.services import ChatService
from app.repositories import ChatStorage

router = APIRouter()

# This will be set by the main app
chat_storage = None
chat_service = None


def set_dependencies(storage: ChatStorage):
    """Set dependencies for the router"""
    global chat_storage, chat_service
    chat_storage = storage
    chat_service = ChatService(storage)


@router.post("/chatrooms")
async def create_chatroom():
    """새 채팅방 생성 (파라미터 없음)"""
    try:
        chatroom = chat_storage.create_chatroom()
        return chatroom  # 직접 chatroom 객체 반환
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅방 생성 실패: {str(e)}")


@router.get("/chatrooms")
async def get_chatrooms():
    """모든 채팅방 조회 (API 명세에 맞는 형식)"""
    try:
        print(f"🔍 Getting all chatrooms. Total chatrooms in storage: {len(chat_storage.chatrooms)}")
        chatrooms = chat_storage.get_all_chatrooms()
        print(f"📋 Returning {len(chatrooms)} chatrooms: {chatrooms}")
        return {"chatrooms": chatrooms}
    except Exception as e:
        print(f"❌ Error getting chatrooms: {e}")
        raise HTTPException(status_code=500, detail=f"채팅방 조회 실패: {str(e)}")


@router.get("/chatrooms/{chatroom_id}/history")
async def get_chatroom_history(chatroom_id: int):
    """채팅방 히스토리 조회 (API 명세에 맞는 형식)"""
    try:
        history = chat_storage.get_chatroom_history(chatroom_id)
        if not history:
            raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
        
        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅방 히스토리 조회 실패: {str(e)}")


@router.delete("/chatrooms/{chatroom_id}")
async def delete_chatroom(chatroom_id: int):
    """채팅방 삭제"""
    try:
        success = chat_storage.delete_chatroom(chatroom_id)
        if not success:
            raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
        
        return {"success": True, "message": "채팅방이 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅방 삭제 실패: {str(e)}")


@router.put("/chatrooms/{chatroom_id}/name")
async def update_chatroom_name(chatroom_id: int, request: UpdateChatRoomNameRequest):
    """채팅방 이름 수정"""
    try:
        updated_chatroom = chat_storage.update_chatroom_name(chatroom_id, request.name)
        if not updated_chatroom:
            raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
        
        return {"success": True, "message": "채팅방 이름이 수정되었습니다.", "chatroom": updated_chatroom}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅방 이름 수정 실패: {str(e)}")


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """스트리밍 채팅 API 엔드포인트"""
    
    async def generate():
        try:
            async for chunk in chat_service.process_chat_request(request.choice, request.message, request.chatroom_id):
                yield chunk
        except Exception as e:
            import json
            error_response = {"msg": f"서버 내부 오류: {str(e)}"}
            yield f"data: {json.dumps(error_response)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/edit_message")
async def edit_message_endpoint(request: EditMessageRequest):
    """메시지 수정 API 엔드포인트"""
    try:
        result = chat_service.process_edit_request(
            request.choice, 
            request.message, 
            request.chatroom_id, 
            request.original_chat_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메시지 수정 실패: {str(e)}")
