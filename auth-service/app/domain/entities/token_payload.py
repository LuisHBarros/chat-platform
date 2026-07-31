from dataclasses import dataclass
from typing import Literal
from uuid import UUID


TokenType = Literal["access", "refresh"]


@dataclass(frozen=True, slots=True)
class TokenPayload:
    user_id: UUID
    token_type: TokenType
