from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

TokenType = Literal["access", "refresh"]


@dataclass(frozen=True, slots=True)
class TokenPayload:
    user_id: UUID
    jti: UUID
    expires_at: datetime
    token_type: TokenType


@dataclass(frozen=True, slots=True)
class IssuedToken:
    token: str
    jti: UUID
    expires_at: datetime
    token_type: TokenType  # optional but useful
