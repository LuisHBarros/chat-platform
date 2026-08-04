from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt

from app.domain.entities.token_payload import IssuedToken, TokenPayload, TokenType
from app.domain.exceptions import AuthenticationError
from app.domain.services.token_service import TokenService


class JwtTokenService(TokenService):
    """Implementation of the TokenService protocol using PyJWT."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 7,
    ) -> None:
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    def create_access_token(self, user_id: UUID) -> IssuedToken:
        jti = uuid4()
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": str(user_id),
            "jti": str(jti),
            "exp": expires_at,
            "iat": now,
            "type": "access",
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        return IssuedToken(
            token=token,
            jti=jti,
            expires_at=expires_at,
            token_type="access",
        )

    def create_refresh_token(self, user_id: UUID) -> IssuedToken:
        jti = uuid4()
        now = datetime.now(UTC)
        expires_at = now + timedelta(days=self.refresh_token_expire_days)

        payload = {
            "sub": str(user_id),
            "jti": str(jti),
            "exp": expires_at,
            "iat": now,
            "type": "refresh",
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        return IssuedToken(
            token=token,
            jti=jti,
            expires_at=expires_at,
            token_type="refresh",
        )

    def decode(self, token: str) -> TokenPayload:
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            raw_type = payload.get("type") or payload.get("token_type")
            if raw_type not in ("access", "refresh"):
                raise AuthenticationError("Invalid token type in payload")

            token_type: TokenType = raw_type  # type: ignore[assignment]
            user_id = UUID(payload["sub"])
            jti = UUID(payload["jti"])
            exp_timestamp = payload["exp"]
            expires_at = datetime.fromtimestamp(exp_timestamp, tz=UTC)

            return TokenPayload(
                user_id=user_id,
                jti=jti,
                expires_at=expires_at,
                token_type=token_type,
            )
        except jwt.PyJWTError as exc:
            raise AuthenticationError(f"Invalid or expired token: {exc}") from exc
        except (KeyError, ValueError) as exc:
            raise AuthenticationError(f"Malformed token payload: {exc}") from exc


PyJWTTokenService = JwtTokenService
