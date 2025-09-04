"""
Conversation session repository - Manages conversation state in PostgreSQL
"""

from typing import Tuple, Optional, Dict, Any
import json
import logging

from app.database import db_connection
from app.new_logic_sugg import SessionContext, ConversationState


logger = logging.getLogger(__name__)


class ConversationSessionRepo:
    """PostgreSQL 기반 대화 세션 저장소"""

    def get_or_create(self, chatroom_id: int, user_id: str) -> Tuple[SessionContext, int]:
        """세션이 있으면 로드, 없으면 초기 상태로 생성 후 반환"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT state, current_module, extracted_params, last_executed_module,
                           modification_attempts, version
                    FROM service_conversation_sessions
                    WHERE chatroom_id = %s AND user_id = %s
                    """,
                    (chatroom_id, user_id),
                )
                row = cursor.fetchone()
                if row:
                    ctx = SessionContext(
                        state=ConversationState(row["state"]),
                        current_module=row["current_module"],
                        extracted_params=row["extracted_params"],
                        last_executed_module=row["last_executed_module"],
                        modification_attempts=row["modification_attempts"] or 0,
                    )
                    return ctx, row["version"]

                # 없으면 생성
                cursor.execute(
                    """
                    INSERT INTO service_conversation_sessions
                        (chatroom_id, user_id, state, version, updated_at)
                    VALUES (%s, %s, %s, 0, CURRENT_TIMESTAMP)
                    RETURNING state, current_module, extracted_params, last_executed_module, modification_attempts, version
                    """,
                    (chatroom_id, user_id, ConversationState.INITIAL.value),
                )
                row = cursor.fetchone()
                ctx = SessionContext(
                    state=ConversationState(row["state"]),
                    current_module=row["current_module"],
                    extracted_params=row["extracted_params"],
                    last_executed_module=row["last_executed_module"],
                    modification_attempts=row["modification_attempts"] or 0,
                )
                return ctx, row["version"]
        except Exception as e:
            logger.error(f"Failed to get_or_create conversation session chatroom={chatroom_id}, user={user_id}: {e}")
            raise

    def save(self, chatroom_id: int, user_id: str, ctx: SessionContext, expected_version: int) -> None:
        """낙관적 락으로 상태 저장, 동시성 충돌 시 예외 발생"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE service_conversation_sessions
                    SET state = %s,
                        current_module = %s,
                        extracted_params = %s,
                        last_executed_module = %s,
                        modification_attempts = %s,
                        version = version + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE chatroom_id = %s AND user_id = %s AND version = %s
                    """,
                    (
                        ctx.state.value,
                        ctx.current_module,
                        json.dumps(ctx.extracted_params) if ctx.extracted_params is not None else None,
                        ctx.last_executed_module,
                        ctx.modification_attempts,
                        chatroom_id,
                        user_id,
                        expected_version,
                    ),
                )

                if cursor.rowcount == 0:
                    raise RuntimeError("ConcurrentUpdateError")
        except Exception as e:
            logger.error(f"Failed to save conversation session chatroom={chatroom_id}, user={user_id}: {e}")
            raise


