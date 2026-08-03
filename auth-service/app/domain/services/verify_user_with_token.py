from datetime import datetime, timezone

from app.domain.exceptions import ValidationError
from app.domain.repositories import UserRepository
from app.domain.repositories.verification_token_repository import VerificationTokenRepository


class VerifyUserWithToken:
    def __init__(self, user_repository: UserRepository, token_verification_repository: VerificationTokenRepository):
        self.token_verification_repository = token_verification_repository
        self.user_repository = user_repository

    async def execute(self, token_str: str):
        if not token_str:
            raise ValidationError("Token is required")

        now = datetime.now(timezone.utc)

        token = await self.token_verification_repository.get_by_token(token_str, "email_verification")
        if token is None or not token.is_valid(now):
            raise ValidationError("Invalid or expired token")

        user = await self.user_repository.get_by_id(token.user_id)
        if user is None:
            raise ValidationError("User associated with token was not found")

        verified_user = user.verify(now)
        used_token = token.mark_as_used(now)

        await self.token_verification_repository.save(used_token)
        return await self.user_repository.save(verified_user)