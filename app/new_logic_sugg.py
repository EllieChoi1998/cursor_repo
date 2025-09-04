"""
AI 서비스 백엔드 - 파라미터 수정 로직 확장 방안

기존 구조를 최대한 유지하면서 파라미터 수정 대화를 추가하는 방법
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
import json

class ConversationState(Enum):
    INITIAL = "initial"  # 최초 질의 상태
    PARAMETER_CONFIRMATION = "parameter_confirmation"  # 파라미터 확인 상태
    PARAMETER_MODIFICATION = "parameter_modification"  # 파라미터 수정 상태
    EXECUTION_READY = "execution_ready"  # 실행 준비 완료

@dataclass
class SessionContext:
    """세션별 대화 상태 관리"""
    state: ConversationState
    current_module: Optional[str] = None
    extracted_params: Optional[Dict[str, Any]] = None
    last_executed_module: Optional[str] = None
    modification_attempts: int = 0  # 수정 시도 횟수 (무한루프 방지)

class AIBackendLogic:
    def __init__(self):
        # 연속 실행 가능 모듈 매핑
        self.continuation_modules = {
            "lot_start": ["lot_point"],
            "sameness": ["sameness_to_trend"],
            "commonality": ["commonality_to_trend"],
            "lot_hold_pe_confirm_module": ["lot_hold", "pe_confirm"]  # 분리 가능
        }
        
        # 세션별 컨텍스트 저장 (실제로는 Redis나 DB에 저장)
        self.sessions = {}

    def process_user_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """메인 메시지 처리 로직"""
        
        # 세션 컨텍스트 가져오기 또는 생성
        if user_id not in self.sessions:
            self.sessions[user_id] = SessionContext(ConversationState.INITIAL)
        
        context = self.sessions[user_id]
        
        # 상태별 처리 분기
        if context.state == ConversationState.INITIAL:
            return self._handle_initial_query(user_id, message, context)
        
        elif context.state == ConversationState.PARAMETER_CONFIRMATION:
            return self._handle_parameter_confirmation(user_id, message, context)
        
        elif context.state == ConversationState.PARAMETER_MODIFICATION:
            return self._handle_parameter_modification(user_id, message, context)
        
        else:
            # 예외 상황 - 초기 상태로 리셋
            context.state = ConversationState.INITIAL
            return self._handle_initial_query(user_id, message, context)

    def _handle_initial_query(self, user_id: str, message: str, context: SessionContext) -> Dict[str, Any]:
        """최초 질의 처리 (기존 로직)"""
        
        # 1단계: 지시사 체크 (기존 로직)
        has_demonstratives = self._check_demonstratives(message)
        
        if not has_demonstratives:
            # 신규 모듈 호출 인식
            llm_response = self._call_llm_for_module_detection(message)
            
            if llm_response == "YES":
                # 모듈 식별
                module_name = self._call_llm_for_module_identification(message)
                context.current_module = module_name
                
                # 파라미터 추출
                extracted_params = self._call_llm_for_parameter_extraction(message, module_name)
                context.extracted_params = extracted_params
                
                # 상태 변경: 파라미터 확인 단계로
                context.state = ConversationState.PARAMETER_CONFIRMATION
                
                return {
                    "response": f"이 조건으로 분석하시겠습니까?\n\n{json.dumps(extracted_params, indent=2, ensure_ascii=False)}\n\n만일 틀렸다면 다시 말씀해 주세요.",
                    "requires_confirmation": True,
                    "module": module_name,
                    "params": extracted_params
                }
            
            else:  # NO인 경우
                return self._handle_no_response(user_id, message, context)
        
        else:
            # 지시사가 있는 경우 기존 로직
            return self._handle_continuation_or_modification(user_id, message, context)

    def _handle_parameter_confirmation(self, user_id: str, message: str, context: SessionContext) -> Dict[str, Any]:
        """파라미터 확인 단계 처리 - 여기가 핵심!"""
        
        # 사용자 응답 분석
        confirmation_result = self._analyze_user_confirmation(message)
        
        if confirmation_result == "APPROVED":
            # 사용자가 승인 → 모듈 실행
            context.state = ConversationState.EXECUTION_READY
            result = self._execute_module(context.current_module, context.extracted_params)
            
            # 실행 완료 후 상태 초기화
            context.last_executed_module = context.current_module
            context.state = ConversationState.INITIAL
            context.current_module = None
            context.extracted_params = None
            
            return {
                "response": "모듈 실행이 완료되었습니다.",
                "execution_result": result,
                "executed_module": context.last_executed_module
            }
        
        elif confirmation_result == "MODIFICATION_REQUESTED":
            # 사용자가 수정 요청 → 수정 모드로
            context.state = ConversationState.PARAMETER_MODIFICATION
            context.modification_attempts += 1
            
            if context.modification_attempts > 3:  # 무한루프 방지
                context.state = ConversationState.INITIAL
                return {"response": "수정 시도가 너무 많습니다. 처음부터 다시 시작해주세요."}
            
            return {
                "response": "어떤 부분을 수정하시겠습니까? 구체적으로 말씀해 주세요.",
                "modification_mode": True,
                "current_params": context.extracted_params
            }
        
        else:
            # 애매한 응답인 경우
            return {
                "response": "죄송합니다. '네, 맞습니다' 또는 '아니요, 수정해주세요'와 같이 명확하게 답변해 주세요.",
                "requires_confirmation": True
            }

    def _handle_parameter_modification(self, user_id: str, message: str, context: SessionContext) -> Dict[str, Any]:
        """파라미터 수정 단계 처리"""
        
        try:
            # 기존 파라미터와 사용자 수정 요청을 합쳐서 새로운 파라미터 생성
            updated_params = self._call_llm_for_parameter_update(
                original_params=context.extracted_params,
                modification_request=message,
                module_name=context.current_module
            )
            
            context.extracted_params = updated_params
            context.state = ConversationState.PARAMETER_CONFIRMATION
            
            return {
                "response": f"수정된 조건입니다. 이대로 진행하시겠습니까?\n\n{json.dumps(updated_params, indent=2, ensure_ascii=False)}\n\n맞으면 '네'라고, 또 수정이 필요하면 구체적으로 말씀해 주세요.",
                "requires_confirmation": True,
                "updated_params": updated_params
            }
            
        except Exception as e:
            return {
                "response": f"파라미터 수정 중 오류가 발생했습니다: {str(e)}\n다시 시도해 주세요.",
                "error": True
            }

    def _handle_no_response(self, user_id: str, message: str, context: SessionContext) -> Dict[str, Any]:
        """기존 NO 응답 처리 로직"""
        
        # 직전 실행 모듈 기반 연속 모듈 확인
        if context.last_executed_module and context.last_executed_module in self.continuation_modules:
            available_modules = self.continuation_modules[context.last_executed_module]
            
            # 연속 모듈 또는 부분 실행 체크
            detected_module = self._check_continuation_or_partial_execution(message, available_modules, context.last_executed_module)
            
            if detected_module:
                context.current_module = detected_module
                extracted_params = self._call_llm_for_parameter_extraction(message, detected_module)
                context.extracted_params = extracted_params
                context.state = ConversationState.PARAMETER_CONFIRMATION
                
                return {
                    "response": f"이 조건으로 {detected_module} 모듈을 실행하시겠습니까?\n\n{json.dumps(extracted_params, indent=2, ensure_ascii=False)}\n\n만일 틀렸다면 다시 말씀해 주세요.",
                    "requires_confirmation": True,
                    "module": detected_module,
                    "params": extracted_params
                }
        
        return {"response": "죄송합니다. 요청을 이해하지 못했습니다. 다시 말씀해 주세요."}

    # LLM 호출 메서드들 (실제 구현 시 VLLM 서버 API 호출)
    def _call_llm_for_module_detection(self, message: str) -> str:
        """모듈 호출 여부 감지 LLM (기존)"""
        # 실제로는 VLLM 서버 API 호출
        # return "YES" or "NO"
        pass

    def _call_llm_for_module_identification(self, message: str) -> str:
        """모듈 식별 LLM (기존)"""
        # 실제로는 VLLM 서버 API 호출
        # return module_name like "lot_start", "sameness", etc.
        pass

    def _call_llm_for_parameter_extraction(self, message: str, module_name: str) -> Dict[str, Any]:
        """파라미터 추출 LLM (기존)"""
        # 실제로는 VLLM 서버 API 호출
        # return JSON format parameters
        pass

    def _call_llm_for_parameter_update(self, original_params: Dict[str, Any], modification_request: str, module_name: str) -> Dict[str, Any]:
        """파라미터 업데이트 LLM (신규 추가 필요)"""
        # 새로 추가할 LLM 프롬프트
        # 기존 파라미터 + 수정 요청사항을 분석해서 업데이트된 파라미터 반환
        prompt = f"""
        원본 파라미터: {json.dumps(original_params, ensure_ascii=False)}
        사용자 수정 요청: {modification_request}
        모듈 이름: {module_name}
        
        위 정보를 바탕으로 수정된 파라미터를 JSON 형식으로 반환하세요.
        """
        # 실제로는 VLLM 서버 API 호출
        pass

    def _analyze_user_confirmation(self, message: str) -> str:
        """사용자 확인 응답 분석 (신규 추가 필요)"""
        # 간단한 키워드 매칭 또는 LLM 호출
        message_lower = message.lower().strip()
        
        approval_keywords = ['네', '맞아', '맞습니다', '좋아', '좋습니다', '실행', '진행', '응']
        modification_keywords = ['아니', '틀려', '수정', '바꿔', '다시', '아니야', '변경']
        
        if any(keyword in message_lower for keyword in approval_keywords):
            return "APPROVED"
        elif any(keyword in message_lower for keyword in modification_keywords):
            return "MODIFICATION_REQUESTED"
        else:
            return "UNCLEAR"

    def _check_demonstratives(self, message: str) -> bool:
        """지시사 체크 (기존 로직)"""
        demonstratives = ['여기', '저기', '이제', '이', '저']
        return any(dem in message for dem in demonstratives)

    def _check_continuation_or_partial_execution(self, message: str, available_modules: list, last_module: str) -> str:
        """연속 실행 또는 부분 실행 체크 (기존 로직)"""
        # 기존 로직 구현
        pass

    def _execute_module(self, module_name: str, params: Dict[str, Any]) -> Any:
        """실제 모듈 실행 (기존)"""
        # SQL 함수 호출 및 데이터 반환
        pass

# 사용 예시와 시나리오
if __name__ == "__main__":
    backend = AIBackendLogic()
    
    print("=== 시나리오 1: 신규 모듈 실행 ===")
    user_id = "test_user"
    
    # 1. 최초 질의
    result1 = backend.process_user_message(user_id, "lot_start 모듈로 A라인 데이터 분석해줘")
    print("1단계:", result1)
    
    # 2. 파라미터 수정 요청
    result2 = backend.process_user_message(user_id, "아니야, A라인이 아니라 B라인으로 해줘")
    print("2단계:", result2)
    
    # 3. 최종 승인
    result3 = backend.process_user_message(user_id, "네, 맞습니다. 실행해주세요")
    print("3단계:", result3)
    
    print("\n=== 시나리오 2: 연속성 모듈 실행 ===")
    
    # lot_start 실행 완료 후 연속 모듈 요청
    result4 = backend.process_user_message(user_id, "여기서 포인트 분석도 해줘")  # lot_point 모듈
    print("4단계:", result4)
    
    # 연속성 모듈도 파라미터 확인
    result5 = backend.process_user_message(user_id, "응, 실행해줘")
    print("5단계:", result5)
    
    print("\n=== 시나리오 3: 부분 실행 ===")
    
    # lot_hold_pe_confirm_module 실행 완료 후
    backend.sessions[user_id].last_executed_module = "lot_hold_pe_confirm_module"
    
    result6 = backend.process_user_message(user_id, "여기서 PE CONFIRM MODULE은 제외해줘")
    print("6단계:", result6)
    
    print("\n=== 시나리오 4: 파라미터 확인 중 새로운 질의 인터럽트 ===")
    
    # lot_start 파라미터 확인 대기 중
    backend.sessions[user_id].state = ConversationState.PARAMETER_CONFIRMATION
    backend.sessions[user_id].current_module = "lot_start"
    backend.sessions[user_id].extracted_params = {"line": "A라인", "period": "1주일"}
    
    # 파라미터 확인 중 완전히 다른 새로운 질의
    result8 = backend.process_user_message(user_id, "sameness 모듈로 D라인 분석해줘")
    print("8단계 (새로운 질의):", result8)
    
    print("\n=== 시나리오 5: 파라미터 확인 중 연속성 질의 인터럽트 ===")
    
    # 다시 lot_start 파라미터 확인 대기 상태로 설정
    backend.sessions[user_id].state = ConversationState.PARAMETER_CONFIRMATION
    backend.sessions[user_id].current_module = "lot_start"
    backend.sessions[user_id].last_executed_module = "lot_start"  # 이전 실행 기록
    
    # 파라미터 확인 중 연속성 질의
    result9 = backend.process_user_message(user_id, "여기서 포인트 분석해줘")
    print("9단계 (연속성 질의):", result9)


    def _call_llm_for_interruption_analysis(self, message, context):
    prompt = f"""
    현재 상황: '{context.current_module}' 모듈 파라미터 확인 대기 중
    현재 파라미터: {context.extracted_params}
    사용자 메시지: "{message}"
    
    이 메시지의 의도를 분류하세요:
    1. NEW_QUERY: 새로운 모듈 실행 요청
    2. CONTINUATION_QUERY: 연속 작업 요청
    3. RESPONSE_TO_CONFIRMATION: 현재 파라미터에 대한 응답
    """
