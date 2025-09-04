from typing import Dict, Any

from app.models.conversation_models import ConversationState, SessionContext
from app.repositories.conversation_session import ConversationSessionRepo


class ConversationManager:
    """대화 상태 전이 및 영속화를 담당하는 매니저"""

    def __init__(self, repo: ConversationSessionRepo | None = None):
        self.repo = repo or ConversationSessionRepo()

    def handle(self, chatroom_id: int, user_id: str, message: str) -> Dict[str, Any]:
        """상태 로드→전이→저장까지 수행하고 응답 반환"""
        context, version = self.repo.get_or_create(chatroom_id, user_id)

        # 간단한 상태머신: INITIAL에서만 파라미터 확인으로 이동하는 예시
        if context.state == ConversationState.INITIAL:
            # 여기에서는 간단히 더미 파라미터 추출
            context.current_module = "lot_start"
            context.extracted_params = {"raw": message}
            context.state = ConversationState.PARAMETER_CONFIRMATION
            response = {
                "response": "이 조건으로 분석하시겠습니까?",
                "requires_confirmation": True,
                "module": context.current_module,
                "params": context.extracted_params,
            }
        elif context.state == ConversationState.PARAMETER_CONFIRMATION:
            message_lower = message.lower().strip()
            if any(k in message_lower for k in ["네", "맞", "응", "진행", "실행"]):
                context.state = ConversationState.EXECUTION_READY
                # 실제 모듈 실행은 서비스 계층에서 수행하도록 책임 분리
                response = {"response": "실행 준비 완료", "ready": True}
                # 실행 후 초기화는 서비스가 수행
            elif any(k in message_lower for k in ["아니", "수정", "변경", "다시"]):
                context.state = ConversationState.PARAMETER_MODIFICATION
                context.modification_attempts += 1
                response = {"response": "어떤 부분을 수정할까요?", "modification_mode": True}
            else:
                response = {"response": "명확히 답해주세요 (네/수정)", "requires_confirmation": True}
        elif context.state == ConversationState.PARAMETER_MODIFICATION:
            # 단순히 파라미터에 메시지를 병합
            base = context.extracted_params or {}
            base.update({"mod_request": message})
            context.extracted_params = base
            context.state = ConversationState.PARAMETER_CONFIRMATION
            response = {"response": "수정된 조건입니다. 진행하시겠습니까?", "requires_confirmation": True, "params": base}
        else:
            context.state = ConversationState.INITIAL
            response = {"response": "초기화되었습니다."}

        self.repo.save(chatroom_id, user_id, context, expected_version=version)
        return response


