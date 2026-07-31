from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.entities.object_values import Email, Username, Password


@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    email: Email
    username: Username
    password: Password
    is_active: bool
    is_verified: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        email: Email,
        username: Username,
        password: Password,
        now: datetime,
        is_superuser: bool = False,
    ) -> User:
        return cls(
            id=uuid4(),
            email=email,
            username=username,
            password=password,
            is_active=True,
            is_verified=False,
            is_superuser=is_superuser,
            created_at=now,
            updated_at=now,
        )

    def can_authenticate(self) -> bool:
        return self.is_active and self.is_verified

    def verify(self, now: datetime) -> User:
        if self.is_verified:
            return self
        return replace(self, is_verified=True, updated_at=now)

    def deactivate(self, now: datetime) -> User:
        return replace(self, is_active=False, updated_at=now)

    def activate(self, now: datetime) -> User:
        return replace(self, is_active=True, updated_at=now)

    def change_password(self, password: Password, now: datetime) -> User:
        return replace(self, password=password, updated_at=now)
