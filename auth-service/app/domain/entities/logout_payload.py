from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

TokenType = Literal["access", "refresh"]

@dataclass(frozen=True, slots=True)
class LogoutPayload:
    user_id: UUID
    token_type: TokenType
    expires_at: datetime
