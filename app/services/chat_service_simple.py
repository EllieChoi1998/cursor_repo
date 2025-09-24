"""
Simplified chat service - Handles chat processing business logic
"""

import json
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from app.models import BotResponse
from app.repositories import ChatStorage
from app.services.data_generators import DataGenerators
from app.services.query_analyzer import QueryAnalyzer
from app.services.conversation_manager import ConversationManager

# Import plotly spec generator
try:
    from .plotlyjs_spec_writer import generate_plotly_spec
except ImportError:
    def generate_plotly_spec(message):
        return {"error": "plotlyjs_spec_writer not available"}


class ChatService:
    """채팅 서비스"""
    
    def __init__(self, chat_storage: ChatStorage):
        self.chat_storage = chat_storage
        self.data_generators = DataGenerators()
        self.query_analyzer = QueryAnalyzer()
        self.conversation_manager = ConversationManager()

    async def process_chat_request(self, choice: str, message: str, chatroom_id: int, user_id: str):
        """채팅 요청 처리 (user_id 파라미터 추가)"""
        # 채팅방 확인
        chatroom = self.chat_storage.get_chatroom(chatroom_id)
        if not chatroom:
            yield f"data: {json.dumps({'msg': '존재하지 않는 채팅방입니다.'})}\n\n"
            return
        
        # 먼저 대화 상태 전이/확인 응답을 처리
        convo_response = self.conversation_manager.handle(chatroom_id, user_id, message)
        if convo_response.get('requires_confirmation') or convo_response.get('modification_mode'):
            yield f"data: {json.dumps({'msg': convo_response['response'], 'conversation': convo_response})}\n\n"
            return
        # 실행 준비 신호면 이후 데이터 처리로 진입

        # choice 파라미터를 우선적으로 고려하여 질의 분석
        detected_type, command_type, error_msg = self.query_analyzer.analyze_query_with_choice(choice, message)
        
        print(f"🔍 DEBUG: choice='{choice}', message='{message}'")
        print(f"🔍 DEBUG: detected_type='{detected_type}', command_type='{command_type}', error_msg='{error_msg}'")
        
        if error_msg:
            # 실패한 메시지는 저장하지 않고 에러만 반환
            yield f"data: {json.dumps({'msg': error_msg})}\n\n"
            return
        
        # 사용자 메시지 시간 기록
        user_message_time = datetime.now()
        
        # 유효한 메시지만 저장 (user_id 파라미터 추가)
        user_message = self.chat_storage.add_message(chatroom_id, user_id, message, 'user', detected_type)
        
        # 처리 시작 메시지
        yield f"data: {json.dumps({'progress_message': '🔄 메시지를 처리하는 중...'})}\n\n"
        await asyncio.sleep(0.3)
        
        # 분석 시작 메시지
        yield f"data: {json.dumps({'progress_message': '⚙️ 데이터를 분석하고 있습니다...'})}\n\n"
        await asyncio.sleep(0.2)
        
        # 백엔드가 결정한 데이터 타입별 처리
        response = None
        
        try:
            if detected_type == 'pcm':
                response = await self._process_pcm_type(command_type, message, chatroom_id)
                
            elif detected_type == 'two':
                response = await self._process_two_tables_type(command_type, message, chatroom_id)
                
            elif detected_type == 'inline':
                response = await self._process_inline_type(command_type, message, chatroom_id)
                
            elif detected_type == 'rag':
                response = await self._process_rag_type(command_type, message, chatroom_id)
                
            # 각 타입별 진행 메시지 전송
            if detected_type == 'pcm':
                yield f"data: {json.dumps({'progress_message': f'📈 PCM {command_type.upper()} 데이터를 생성하고 있습니다...'})}\n\n"
                await asyncio.sleep(0.3)
            elif detected_type == 'two':
                yield f"data: {json.dumps({'progress_message': '📊 TWO TABLES 데이터를 생성하고 있습니다...'})}\n\n"
                await asyncio.sleep(0.3)
            elif detected_type == 'inline':
                yield f"data: {json.dumps({'progress_message': f'📊 INLINE {command_type.upper()} 데이터를 생성하고 있습니다...'})}\n\n"
                await asyncio.sleep(0.3)
            elif detected_type == 'rag':
                yield f"data: {json.dumps({'progress_message': '🔍 RAG 데이터를 검색하고 있습니다...'})}\n\n"
                await asyncio.sleep(0.3)
                    
        except Exception as e:
            yield f"data: {json.dumps({'msg': f'데이터 처리 중 오류가 발생했습니다: {str(e)}'})}\n\n"
            return
        
        if response is None:
            yield f"data: {json.dumps({'msg': '처리할 수 없는 요청입니다.'})}\n\n"
            return
        
        # 성공한 경우에만 저장 (user_id 파라미터 추가)
        bot_response = self.chat_storage.add_response(user_message.id, chatroom_id, user_id, response)
        
        # real_data를 제외한 response 데이터 생성 (채팅 히스토리용)
        history_response = response.copy()
        if 'real_data' in history_response:
            del history_response['real_data']
        
        print(f"📝 Saving to chat history (real_data excluded): {json.dumps(history_response, indent=2)}")
        print(f"📝 JSON string being saved: {json.dumps(history_response)}")
        
        # 봇 응답 시간 기록
        bot_response_time = datetime.now()
        
        # 채팅 히스토리에 추가 (real_data 제외) - 실제 시간 사용 (user_id 파라미터 추가)
        chat_history = self.chat_storage.add_chat_history(
            chatroom_id, 
            user_id,
            message, 
            json.dumps(history_response),
            user_time=user_message_time,
            response_time=bot_response_time
        )
        print(f"📝 Chat history saved with chat_id: {chat_history.chat_id}")
        print(f"📝 Bot response in chat history: {chat_history.bot_response}")
        print(f"📅 User message time: {user_message_time}, Bot response time: {bot_response_time}")
        
        # 최종 응답 - 실제 chat_id 사용
        chat_response = {
            'chat_id': chat_history.chat_id,  # 실제 생성된 chat_id 사용
            'message_id': user_message.id,
            'response_id': bot_response.id,
            'response': response
        }
        
        print(f"📤 Sending chat response with chat_id: {chat_history.chat_id}")
        
        # 응답 데이터 크기 확인
        response_json = json.dumps(chat_response)
        print(f"📤 Response JSON size: {len(response_json)} characters")
        
        # real_data 크기 확인
        if 'real_data' in response and response['real_data']:
            real_data_size = len(json.dumps(response['real_data']))
            print(f"📤 Real data size: {real_data_size} characters")
            print(f"📤 Real data records: {len(response['real_data'])}")
        
        yield f"data: {response_json}\n\n"

    async def _process_pcm_type(self, command_type: str, message: str, chatroom_id: int) -> Dict[str, Any]:
        """PCM 타입 처리"""
        if command_type == 'trend':
            data = self.data_generators.generate_pcm_trend_data()
            total_records = len(data) if isinstance(data, list) else 0
            device_types = []
            date_range = "N/A"
            
            if isinstance(data, list) and len(data) > 0:
                device_types = list(set(row.get('DEVICE', 'Unknown') for row in data if isinstance(row, dict)))
                date_ids = [row.get('DATE_WAFER_ID', 0) for row in data if isinstance(row, dict) and row.get('DATE_WAFER_ID')]
                if date_ids:
                    date_range = f"{min(date_ids)} - {max(date_ids)}"
            
            success_message = f"✅ PCM TREND 데이터를 성공적으로 받았습니다!\n• Result Type: lot_start\n• Total Records: {total_records}\n• Chat ID: {chatroom_id}\n\nChart Summary:\n• Device Types: {', '.join(device_types) if device_types else 'N/A'}\n• Date Range: {date_range}"
            
            return {
                'result': 'lot_start',
                'real_data': data,
                'sql': 'SELECT * FROM pcm_data WHERE date >= "2024-01-01" ORDER BY date_wafer_id',
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }
            
        elif command_type == 'commonality':
            data, commonality_info = self.data_generators.generate_commonality_data()
            success_message = f"✅ COMMONALITY 데이터를 성공적으로 받았습니다!\n• Result Type: commonality\n• Total Records: {len(data) if isinstance(data, list) else sum(len(v) if isinstance(v, list) else 0 for v in data.values()) if isinstance(data, dict) else 0}\n• Chat ID: {chatroom_id}"
            
            return {
                'result': 'commonality',
                'real_data': data,
                'commonality_info': commonality_info,
                'sql': 'SELECT * FROM pcm_data WHERE type = "commonality"',
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }
            
        elif command_type == 'sameness':
            data, _ = self.data_generators.generate_commonality_data()
            success_message = f"✅ SAMENESS 데이터를 성공적으로 받았습니다!\n• Result Type: sameness\n• Total Records: {len(data) if isinstance(data, list) else sum(len(v) if isinstance(v, list) else 0 for v in data.values()) if isinstance(data, dict) else 0}\n• Chat ID: {chatroom_id}"
            
            return {
                'result': 'sameness',
                'real_data': data,
                'sql': 'SELECT * FROM pcm_data WHERE type = "sameness"',
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }
            
        elif command_type == 'point':
            data = self.data_generators.generate_pcm_point_data()
            total_records = len(data) if isinstance(data, list) else 0
            pcm_sites = []
            date_range = "N/A"
            
            if isinstance(data, list) and len(data) > 0:
                pcm_sites = list(set(row.get('PCM_SITE', 'Unknown') for row in data if isinstance(row, dict)))
                date_ids = [row.get('DATE_WAFER_ID', 0) for row in data if isinstance(row, dict) and row.get('DATE_WAFER_ID')]
                if date_ids:
                    date_range = f"{min(date_ids)} - {max(date_ids)}"
            
            success_message = f"✅ PCM POINT 데이터를 성공적으로 받았습니다!\n• Result Type: lot_point\n• Total Records: {total_records}\n• Chat ID: {chatroom_id}\n\nChart Summary:\n• PCM Sites: {', '.join(pcm_sites) if pcm_sites else 'N/A'}\n• Date Range: {date_range}"
            
            return {
                'result': 'lot_point',
                'real_data': data,
                'sql': 'SELECT * FROM pcm_data WHERE type = "point"',
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }
            
        elif command_type in ['sameness_to_trend', 'commonality_to_trend', 'to_trend']:
            data = self.data_generators.generate_pcm_to_trend_data()
            total_records = 0
            if isinstance(data, list):
                total_records = len(data)
            elif isinstance(data, dict):
                total_records = sum(len(v) if isinstance(v, list) else 0 for v in data.values())
            
            result_type = command_type if command_type in ['sameness_to_trend', 'commonality_to_trend'] else 'pcm_to_trend'
            success_message = f"✅ {result_type.upper()} 데이터를 성공적으로 받았습니다!\n• Result Type: {result_type}\n• Total Records: {total_records}\n• Chat ID: {chatroom_id}"
            
            return {
                'result': result_type,
                'real_data': data,
                'sql': f'SELECT * FROM pcm_to_trend WHERE type = "{command_type.split("_")[0]}"',
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }
        
        return None

    async def _process_two_tables_type(self, command_type: str, message: str, chatroom_id: int) -> Dict[str, Any]:
        """Two Tables 타입 처리"""
        if command_type in ['two_tables', 'two_tables_empty_lot', 'two_tables_empty_pe', 'two_tables_empty_both']:
            test_scenario = None
            if command_type == 'two_tables_empty_lot':
                test_scenario = 'empty_lot_hold'
            elif command_type == 'two_tables_empty_pe':
                test_scenario = 'empty_pe_confirm'
            elif command_type == 'two_tables_empty_both':
                test_scenario = 'both_empty'
            
            data = self.data_generators.generate_two_tables_data(test_scenario)
            
            lot_hold_count = 0
            pe_confirm_count = 0
            
            if 'real_data' in data and len(data['real_data']) >= 2:
                lot_hold_data = data['real_data'][0].get('lot_hold_module', [])
                pe_confirm_data = data['real_data'][1].get('pe_confirm_module', [])
                lot_hold_count = len(lot_hold_data) if isinstance(lot_hold_data, list) else 0
                pe_confirm_count = len(pe_confirm_data) if isinstance(pe_confirm_data, list) else 0
            
            success_message = f"✅ TWO TABLES 데이터를 성공적으로 받았습니다!\n• Result Type: lot_hold_pe_confirm_module\n• Lot Hold Records: {lot_hold_count}\n• PE Confirm Records: {pe_confirm_count}\n• Chat ID: {chatroom_id}"
            
            return {
                'result': 'lot_hold_pe_confirm_module',
                'real_data': data['real_data'],
                'sql': 'SELECT * FROM lot_hold_table, pe_confirm_table',
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }
        
        return None

    async def _process_inline_type(self, command_type: str, message: str, chatroom_id: int) -> Dict[str, Any]:
        """Inline 타입 처리"""
        print(f"🎯 DEBUG: Processing inline type with command_type='{command_type}'")
        
        if command_type == 'trend_initial':
            data = self.data_generators.generate_inline_trend_initial_data()
            success_message = f"✅ INLINE TREND INITIAL 데이터를 성공적으로 받았습니다!\n• Result Type: inline_trend_initial\n• Total Records: {len(data) if isinstance(data, list) else 0}\n• Chat ID: {chatroom_id}\n• Criteria: DEVICE"
            
            response = {
                'result': 'inline_trend_initial',
                'criteria': 'DEVICE',
                'real_data': json.dumps(data),
                'success_message': success_message
            }
            print(f"🎯 DEBUG: Created inline_trend_initial response: {response.keys()}")
            return response
            
        elif command_type == 'cpk_achieve_rate_initial':
            # CPK 달성률 초기 분석 데이터 생성
            data = self.data_generators.generate_cpk_achieve_rate_data()
            success_message = f"✅ CPK 달성률 분석 데이터를 성공적으로 받았습니다!\n• Result Type: cpk_achieve_rate_initial\n• Total Records: {len(data) if isinstance(data, list) else 0}\n• Chat ID: {chatroom_id}"
            
            response = {
                'result': 'cpk_achieve_rate_initial',
                'real_data': json.dumps(data),
                'success_message': success_message
            }
            print(f"🎯 DEBUG: Created cpk_achieve_rate_initial response: {response.keys()}")
            return response
            
        elif command_type == 'trend_followup':
            if "spec" in message.split(" "):
                llm_spec = generate_plotly_spec(message)
                print(f"🎯 DEBUG: LLM Spec: {llm_spec}")
                data = self.data_generators.generate_inline_trend_initial_data()
                success_message = f"✅ INLINE TREND FOLLOWUP Plotly Spec을 성공적으로 받았습니다!\n• Result Type: inline_trend_followup_spec\n• Chat ID: {chatroom_id}"
                return {
                    'result': 'inline_trend_followup',
                    'real_data': json.dumps(data),
                    'llm_spec': json.dumps(llm_spec),
                    'success_message': success_message
                }
            else:
                criteria = 'PARA'
                message_lower = message.lower()
                
                if 'main_eq' in message_lower:
                    criteria = 'MAIN_EQ'
                elif 'eq_cham' in message_lower:
                    criteria = 'EQ_CHAM'
                elif 'device' in message_lower:
                    criteria = 'DEVICE'
                elif 'route' in message_lower:
                    criteria = 'ROUTE'
                elif 'oper' in message_lower:
                    criteria = 'OPER'
                elif 'para' in message_lower:
                    criteria = 'PARA'
                
                print(f"🎯 Extracted criteria: {criteria} from message: {message}")
                
                data = self.data_generators.generate_inline_trend_followup_data(criteria)
                success_message = f"✅ INLINE TREND FOLLOWUP 데이터를 성공적으로 받았습니다!\n• Result Type: inline_trend_followup\n• Total Records: {len(data) if isinstance(data, list) else 0}\n• Chat ID: {chatroom_id}\n• Criteria: {criteria}"
                
                return {
                    'result': 'inline_trend_followup',
                    'criteria': criteria,
                    'real_data': json.dumps(data),
                    'success_message': success_message
                }
                
        elif command_type in ['analysis', 'performance']:
            data = self.data_generators.generate_inline_analysis_data()
            result_type = f"inline_{command_type}"
            success_message = f"✅ INLINE {command_type.upper()} 데이터를 성공적으로 받았습니다!\n• Result Type: {result_type}\n• Total Records: {len(data) if isinstance(data, list) else 0}\n• Chat ID: {chatroom_id}"
            
            return {
                'result': result_type,
                'real_data': data,
                'sql': f'SELECT * FROM inline_{command_type} WHERE date >= "2024-01-01"',
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }
        
        return None

    async def _process_rag_type(self, command_type: str, message: str, chatroom_id: int) -> Dict[str, Any]:
        """RAG 타입 처리"""
        if command_type == 'search':
            answer = self.data_generators.generate_rag_answer_data()
            success_message = f"✅ RAG 파일 검색이 완료되었습니다!\n• Result Type: rag\n• Found Files: {len(answer) if isinstance(answer, list) else 0}\n• Chat ID: {chatroom_id}"
            
            return {
                'result': 'rag',
                'files': answer,
                'response': None,
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }
        else:
            response_text = f"'{message}'에 대한 답변입니다. 요청하신 내용을 분석하여 적절한 정보를 제공드립니다."
            success_message = f"✅ RAG 답변 생성이 완료되었습니다!\n• Result Type: rag\n• Response Length: {len(response_text)} characters\n• Chat ID: {chatroom_id}"
            
            return {
                'result': 'rag',
                'files': None,
                'response': response_text,
                'timestamp': datetime.now().isoformat(),
                'success_message': success_message
            }

    def process_edit_request(self, choice: str, message: str, chatroom_id: int, original_chat_id: int, user_id: str) -> Dict[str, Any]:
        """메시지 수정 요청 처리 (user_id 파라미터 추가)"""
        existing_chat_id = original_chat_id
        print(f"🔧 Using existing chat_id: {existing_chat_id}")
        
        detected_type, command_type, error_msg = self.query_analyzer.analyze_query_with_choice(choice, message)
        print(f"🔍 Edit message analysis - Type: {detected_type}, Command: {command_type}, Error: {error_msg}")
        
        if error_msg:
            raise ValueError(error_msg)
        
        # 동기식으로 처리하기 위해 별도 메서드 사용
        response = self._process_edit_sync(detected_type, command_type, message)
        
        if response is None:
            raise ValueError("처리할 수 없는 요청입니다.")
        
        # 응답 저장 (user_id 파라미터 추가)
        response_id = str(uuid.uuid4())
        bot_response = BotResponse(
            id=response_id,
            message_id=str(existing_chat_id),
            chatroom_id=chatroom_id,
            user_id=user_id,
            content=response,
            timestamp=datetime.now()
        )
        self.chat_storage.responses[response_id] = bot_response
        
        # 히스토리 업데이트
        history_response = response.copy()
        if 'real_data' in history_response:
            del history_response['real_data']
        
        existing_history = self.chat_storage.edit_chat_history(
            chatroom_id, 
            existing_chat_id, 
            user_id,
            message, 
            json.dumps(history_response)
        )
        
        if not existing_history:
            existing_history = self.chat_storage.add_chat_history(
                chatroom_id,
                user_id,
                message,
                json.dumps(history_response),
                user_time=datetime.now(),
                response_time=datetime.now()
            )
            existing_history.chat_id = existing_chat_id
            print(f"✅ Created new chat history with existing chat_id: {existing_chat_id}")
        
        return {
            'success': True,
            'message': '메시지가 성공적으로 수정되었습니다.',
            'chat_id': existing_chat_id,
            'response_id': bot_response.id,
            'response': response
        }

    def _process_edit_sync(self, detected_type: str, command_type: str, message: str) -> Dict[str, Any]:
        """동기식 편집 처리"""
        if detected_type == 'pcm':
            return self._process_pcm_edit_sync(command_type)
        elif detected_type == 'two':
            return self._process_two_tables_edit_sync(command_type)
        elif detected_type == 'inline':
            return self._process_inline_edit_sync(command_type, message)
        elif detected_type == 'rag':
            return self._process_rag_edit_sync(command_type, message)
        return None

    def _process_pcm_edit_sync(self, command_type: str) -> Dict[str, Any]:
        """PCM 수정 동기 처리"""
        if command_type == 'trend':
            data = self.data_generators.generate_pcm_trend_data()
            return {
                'result': 'lot_start',
                'real_data': data,
                'sql': 'SELECT * FROM pcm_data WHERE date >= "2024-01-01" ORDER BY date_wafer_id',
                'timestamp': datetime.now().isoformat()
            }
        elif command_type == 'commonality':
            data, commonality = self.data_generators.generate_commonality_data()
            return {
                'result': 'commonality_start',
                'real_data': data,
                'determined': commonality,
                'SQL': 'SELECT * FROM pcm_data WHERE lot_type IN ("good", "bad")',
                'timestamp': datetime.now().isoformat()
            }
        # ... Add other PCM command types as needed
        return None

    def _process_two_tables_edit_sync(self, command_type: str) -> Dict[str, Any]:
        """Two Tables 수정 동기 처리"""
        if command_type in ['two_tables', 'two_tables_empty_lot', 'two_tables_empty_pe', 'two_tables_empty_both']:
            test_scenario = None
            if command_type == 'two_tables_empty_lot':
                test_scenario = 'empty_lot_hold'
            elif command_type == 'two_tables_empty_pe':
                test_scenario = 'empty_pe_confirm'
            elif command_type == 'two_tables_empty_both':
                test_scenario = 'both_empty'
            
            data = self.data_generators.generate_two_tables_data(test_scenario)
            return {
                'result': 'lot_hold_pe_confirm_module',
                'real_data': data['real_data'],
                'sql': 'SELECT * FROM lot_hold_table, pe_confirm_table',
                'timestamp': datetime.now().isoformat()
            }
        return None

    def _process_inline_edit_sync(self, command_type: str, message: str) -> Dict[str, Any]:
        """Inline 수정 동기 처리"""
        if command_type == 'trend_initial':
            data = self.data_generators.generate_inline_trend_initial_data()
            return {
                'result': 'inline_trend_initial',
                'criteria': 'DEVICE',
                'real_data': json.dumps(data),
                'success_message': f"✅ INLINE TREND INITIAL 데이터를 성공적으로 받았습니다! (Edit Mode)"
            }
        elif command_type == 'cpk_achieve_rate_initial':
            data = self.data_generators.generate_cpk_achieve_rate_data()
            return {
                'result': 'cpk_achieve_rate_initial',
                'real_data': json.dumps(data),
                'success_message': f"✅ CPK 달성률 분석 데이터를 성공적으로 받았습니다! (Edit Mode)"
            }
        elif command_type == 'trend_followup':
            criteria = 'PARA'
            if 'eq_cham' in message.lower():
                criteria = 'EQ_CHAM'
            elif 'route' in message.lower():
                criteria = 'ROUTE'
            elif 'oper' in message.lower():
                criteria = 'OPER'
            
            data = self.data_generators.generate_inline_trend_followup_data(criteria)
            return {
                'result': 'inline_trend_followup',
                'criteria': criteria,
                'real_data': json.dumps(data),
                'success_message': f"✅ INLINE TREND FOLLOWUP 데이터를 성공적으로 받았습니다! (Edit Mode)"
            }
        # ... Add other inline command types as needed
        return None

    def _process_rag_edit_sync(self, command_type: str, message: str) -> Dict[str, Any]:
        """RAG 수정 동기 처리"""
        if command_type == 'search':
            answer = self.data_generators.generate_rag_answer_data()
            return {
                'result': 'rag',
                'files': answer,
                'response': None,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'result': 'rag',
                'files': None,
                'response': f"'{message}'에 대한 답변입니다. 요청하신 내용을 분석하여 적절한 정보를 제공드립니다.",
                'timestamp': datetime.now().isoformat()
            }
        return None
