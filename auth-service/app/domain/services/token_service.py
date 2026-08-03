from typing import Protocol
from uuid import UUID

from app.domain.entities.token_payload import IssuedToken, TokenPayload


class TokenService(Protocol):
    def create_access_token(self, user_id: UUID) -> IssuedToken: ...

    def create_refresh_token(self, user_id: UUID) -> IssuedToken: ...

    def decode(self, token: str) -> TokenPayload: ...
