from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class RefreshToken:
    id: UUID
    user_id: UUID
    jti: UUID
    expires_at: datetime
    created_at: datetime
    revoked_at: datetime | None = None

    @classmethod
    def create(cls, user_id: UUID, jti: UUID, expires_at: datetime, now: datetime) -> RefreshToken:
        return cls(
            id=uuid4(),
            user_id=user_id,
            jti=jti,
            expires_at=expires_at,
            created_at=now,
            revoked_at=None,
        )

    def is_active(self, now: datetime) -> bool:
        from datetime import UTC
        exp = self.expires_at if self.expires_at.tzinfo is not None else self.expires_at.replace(tzinfo=UTC)
        current = now if now.tzinfo is not None else now.replace(tzinfo=UTC)
        return self.revoked_at is None and exp > current

    def revoke(self, now: datetime) -> RefreshToken:
        if self.revoked_at is not None:
            return self
        return replace(self, revoked_at=now)
