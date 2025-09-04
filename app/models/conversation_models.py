from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional


class ConversationState(Enum):
    INITIAL = "initial"
    PARAMETER_CONFIRMATION = "parameter_confirmation"
    PARAMETER_MODIFICATION = "parameter_modification"
    EXECUTION_READY = "execution_ready"


@dataclass
class SessionContext:
    state: ConversationState
    current_module: Optional[str] = None
    extracted_params: Optional[Dict[str, Any]] = None
    last_executed_module: Optional[str] = None
    modification_attempts: int = 0


