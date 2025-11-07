"""
Chat router - Handles all chat-related API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
import json

from app.models import (
    ChatRequest, EditMessageRequest, UpdateChatRoomNameRequest
)
from app.models.chat_models import ExcelAnalysisRequest
from app.services import ChatService
from app.services.excel_analysis_service import ExcelAnalysisService
from app.repositories import ChatStorage
from app.utils.jwt_utils import get_user_id_from_token

router = APIRouter()

# HTTP Bearer 토큰 검증용
security = HTTPBearer(auto_error=False)

# 서비스 초기화
chat_service = ChatService()
excel_analysis_service = ExcelAnalysisService()

# This will be set by the main app
chat_storage = None
chat_service = None

# OPTIONS 요청을 제외하는 의존성 함수
async def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """현재 사용자 정보를 가져오는 의존성 (OPTIONS 요청 제외)"""
    print(f"🔍 get_current_user called: method={request.method}, credentials={credentials is not None}")
    
    # OPTIONS 요청인 경우 None 반환
    if request.method == "OPTIONS":
        print("✅ OPTIONS request detected, skipping authentication")
        return None
    
    # Authorization 헤더가 없는 경우
    if not credentials:
        print("❌ No credentials provided")
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    # JWT 토큰에서 user_id 추출
    user_id = get_user_id_from_token(credentials.credentials)
    if not user_id:
        print("❌ Invalid token")
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    
    print(f"✅ User authenticated: {user_id}")
    return user_id


def set_dependencies(storage: ChatStorage):
    """Set dependencies for the router"""
    global chat_storage, chat_service
    chat_storage = storage
    chat_service = ChatService(storage)


# OPTIONS 요청을 명시적으로 처리하는 엔드포인트들
@router.options("/chatrooms")
async def options_chatrooms():
    """OPTIONS 요청 처리"""
    return {"message": "OK"}


@router.options("/chatrooms/{chatroom_id}/history")
async def options_chatroom_history(chatroom_id: int):
    """OPTIONS 요청 처리"""
    return {"message": "OK"}


@router.options("/chat")
async def options_chat():
    """OPTIONS 요청 처리"""
    return {"message": "OK"}


@router.options("/edit_message")
async def options_edit_message():
    """OPTIONS 요청 처리"""
    return {"message": "OK"}


@router.post("/chatrooms")
async def create_chatroom(user_id: str = Depends(get_current_user)):
    """새 채팅방 생성 (JWT 토큰에서 user_id 추출)"""
    try:
        chatroom = chat_storage.create_chatroom(user_id)
        return chatroom  # 직접 chatroom 객체 반환
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅방 생성 실패: {str(e)}")


@router.get("/chatrooms")
async def get_chatrooms(user_id: str = Depends(get_current_user)):
    """특정 유저의 모든 채팅방 조회 (JWT 토큰에서 user_id 추출)"""
    try:
        print(f"🔍 Getting chatrooms for user: {user_id}. Total chatrooms in storage: {len(chat_storage.chatrooms)}")
        chatrooms = chat_storage.get_all_chatrooms(user_id)
        print(f"📋 Returning {len(chatrooms)} chatrooms for user {user_id}: {chatrooms}")
        return {"chatrooms": chatrooms}
    except Exception as e:
        print(f"❌ Error getting chatrooms: {e}")
        raise HTTPException(status_code=500, detail=f"채팅방 조회 실패: {str(e)}")


@router.get("/chatrooms/{chatroom_id}/history")
async def get_chatroom_history(chatroom_id: int, user_id: str = Depends(get_current_user)):
    """채팅방 히스토리 조회 (JWT 토큰에서 user_id 추출하여 권한 확인)"""
    try:
        history = chat_storage.get_chatroom_history(chatroom_id, user_id)
        if not history:
            raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없거나 접근 권한이 없습니다.")
        
        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅방 히스토리 조회 실패: {str(e)}")


@router.delete("/chatrooms/{chatroom_id}")
async def delete_chatroom(chatroom_id: int, user_id: str = Depends(get_current_user)):
    """채팅방 삭제 (JWT 토큰에서 user_id 추출하여 권한 확인)"""
    try:
        success = chat_storage.delete_chatroom(chatroom_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없거나 삭제 권한이 없습니다.")
        
        return {"success": True, "message": "채팅방이 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅방 삭제 실패: {str(e)}")


@router.put("/chatrooms/{chatroom_id}/name")
async def update_chatroom_name(chatroom_id: int, request: UpdateChatRoomNameRequest, user_id: str = Depends(get_current_user)):
    """채팅방 이름 수정 (JWT 토큰에서 user_id 추출하여 권한 확인)"""
    try:
        updated_chatroom = chat_storage.update_chatroom_name(chatroom_id, request.name, user_id)
        if not updated_chatroom:
            raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없거나 수정 권한이 없습니다.")
        
        return {"success": True, "message": "채팅방 이름이 수정되었습니다.", "chatroom": updated_chatroom}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅방 이름 수정 실패: {str(e)}")


@router.post("/chat")
async def chat_endpoint(request: ChatRequest, user_id: str = Depends(get_current_user)):
    """스트리밍 채팅 API 엔드포인트 (JWT 토큰에서 user_id 추출)"""
    async def generate():
        try:
            async for chunk in chat_service.process_chat_request(request.choice, request.message, request.chatroom_id, user_id):
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
async def edit_message_endpoint(request: EditMessageRequest, user_id: str = Depends(get_current_user)):
    """메시지 수정 API 엔드포인트 (JWT 토큰에서 user_id 추출)"""
    try:
        result = chat_service.process_edit_request(
            request.choice, 
            request.message, 
            request.chatroom_id, 
            request.original_chat_id,
            user_id
        )
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메시지 수정 실패: {str(e)}")


@router.post("/excel_analysis_stream")
async def excel_analysis_stream_endpoint(
    file: UploadFile = File(...),
    message: str = Form(...),
    chatroom_id: int = Form(...),
    user_id: str = Depends(get_current_user)
):
    """엑셀 파일 분석 스트리밍 API 엔드포인트"""
    async def generate():
        try:
            # 진행 상황 메시지
            yield f"data: {json.dumps({'progress_message': '📊 엑셀 파일을 분석하고 있습니다...'})}\n\n"
            
            # 엑셀 파일 분석 수행
            result = await excel_analysis_service.analyze_excel_file(
                file=file,
                prompt=message,
                chatroom_id=chatroom_id,
                user_id=user_id
            )
            
            if not result.get('success', False):
                error_response = {"msg": result.get('error', '분석 실패')}
                yield f"data: {json.dumps(error_response)}\n\n"
                return
            
            # 성공 응답
            yield f"data: {json.dumps({'data': result})}\n\n"
            
        except Exception as e:
            error_response = {"msg": f"엑셀 분석 중 오류가 발생했습니다: {str(e)}"}
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


