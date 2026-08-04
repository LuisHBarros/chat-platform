from typing import Protocol, runtime_checkable

from app.domain.entities.object_values import Email


@runtime_checkable
class EmailService(Protocol):
    """Domain service interface for sending transactional emails."""

    async def send_email(
        self,
        recipient: Email | str,
        subject: str,
        body_html: str,
        body_text: str | None = None,
    ) -> None: ...

    async def send_verification_email(
        self,
        recipient: Email | str,
        token: str,
    ) -> None: ...

    async def send_password_reset_email(
        self,
        recipient: Email | str,
        token: str,
    ) -> None: ...
