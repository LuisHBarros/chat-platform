import secrets
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

TokenType = Literal["email_verification", "password_reset"]


@dataclass(frozen=True, slots=True)
class VerificationToken:
    id: UUID
    user_id: UUID
    token: str
    token_type: TokenType
    expires_at: datetime
    created_at: datetime
    used_at: datetime | None = None

    @classmethod
    def create(
        cls,
        user_id: UUID,
        token_type: TokenType,
        now: datetime,
        ttl_minutes: int = 60,
    ) -> tuple[VerificationToken, str]:
        raw_token = secrets.token_urlsafe(32)
        entity = cls(
            id=uuid4(),
            user_id=user_id,
            token=raw_token,
            token_type=token_type,
            expires_at=now + timedelta(minutes=ttl_minutes),
            created_at=now,
            used_at=None,
        )
        return entity, raw_token

    def is_valid(self, now: datetime) -> bool:
        return self.used_at is None and self.expires_at > now

    def mark_as_used(self, now: datetime) -> VerificationToken:
        if self.used_at is not None:
            return self
        return replace(self, used_at=now)
