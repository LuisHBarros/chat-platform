import asyncio
import os
import smtplib
from email.message import EmailMessage

from app.domain.entities.object_values import Email
from app.domain.exceptions import EmailDeliveryError
from app.domain.services.email_service import EmailService


class SMTPEmailAdapter(EmailService):
    """Concrete implementation of EmailService protocol using SMTP (e.g. MailHog or Production SMTP)."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
        from_email: str | None = None,
        from_name: str | None = None,
        use_tls: bool | None = None,
        use_ssl: bool | None = None,
        timeout: float = 10.0,
        frontend_url: str | None = None,
    ) -> None:
        self.host: str = host or os.getenv("SMTP_HOST") or "localhost"
        self.port: int = port if port is not None else int(os.getenv("SMTP_PORT", "1025"))
        self.username: str | None = username or os.getenv("SMTP_USER")
        self.password: str | None = password or os.getenv("SMTP_PASSWORD")
        self.from_email: str = from_email or os.getenv("SMTP_FROM_EMAIL") or "noreply@discord-like.com"
        self.from_name: str = from_name or os.getenv("SMTP_FROM_NAME") or "Discord-Like Auth"
        self.use_tls: bool = use_tls if use_tls is not None else (os.getenv("SMTP_USE_TLS", "false").lower() == "true")
        self.use_ssl: bool = use_ssl if use_ssl is not None else (os.getenv("SMTP_USE_SSL", "false").lower() == "true")
        self.timeout: float = timeout
        self.frontend_url: str = frontend_url or os.getenv("FRONTEND_URL") or "http://localhost:3000"

    def _send_smtp_message(self, msg: EmailMessage) -> None:
        try:
            if self.use_ssl:
                server_ctx = smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout)
            else:
                server_ctx = smtplib.SMTP(self.host, self.port, timeout=self.timeout)

            with server_ctx as server:
                if self.use_tls and not self.use_ssl:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)
        except Exception as exc:
            raise EmailDeliveryError(f"Failed to send email via SMTP: {exc}") from exc

    async def send_email(
        self,
        recipient: Email | str,
        subject: str,
        body_html: str,
        body_text: str | None = None,
    ) -> None:
        to_address = recipient.value if isinstance(recipient, Email) else str(recipient)

        msg = EmailMessage()
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_address
        msg["Subject"] = subject

        plain_text = body_text or f"Please view this email in an HTML-compatible client.\n\n{body_html}"
        msg.set_content(plain_text)
        msg.add_alternative(body_html, subtype="html")

        await asyncio.to_thread(self._send_smtp_message, msg)

    async def send_verification_email(
        self,
        recipient: Email | str,
        token: str,
    ) -> None:
        verification_url = f"{self.frontend_url}/verify-email?token={token}"

        subject = "Verify Your Account - Discord-Like"
        body_text = (
            f"Welcome to Discord-Like!\n\n"
            f"Please verify your account by clicking the following link:\n{verification_url}\n\n"
            f"If you did not register for an account, please ignore this email."
        )
        body_html = f"""
        <html>
            <body>
                <h2>Welcome to Discord-Like!</h2>
                <p>Please verify your email address to activate your account.</p>
                <p>
                    <a href="{verification_url}" style="background-color: #5865F2; color: white;
                    padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Verify Email</a>
                </p>
                <p>Or copy and paste this link in your browser: <br><code>{verification_url}</code></p>
                <p><small>If you did not request this, please ignore this email.</small></p>
            </body>
        </html>
        """

        await self.send_email(
            recipient=recipient,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
        )

    async def send_password_reset_email(
        self,
        recipient: Email | str,
        token: str,
    ) -> None:
        reset_url = f"{self.frontend_url}/reset-password?token={token}"

        subject = "Reset Your Password - Discord-Like"
        body_text = (
            f"You requested a password reset for your Discord-Like account.\n\n"
            f"Please click the following link to reset your password:\n{reset_url}\n\n"
            f"If you did not request a password reset, please ignore this email."
        )
        body_html = f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>We received a request to reset the password for your Discord-Like account.</p>
                <p>
                    <a href="{reset_url}" style="background-color: #5865F2; color: white;
                    padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Reset Password</a>
                </p>
                <p>Or copy and paste this link in your browser: <br><code>{reset_url}</code></p>
                <p><small>If you did not request a password reset, please ignore this email.</small></p>
            </body>
        </html>
        """

        await self.send_email(
            recipient=recipient,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
        )


EmailAdapter = SMTPEmailAdapter

__all__ = ["EmailAdapter", "SMTPEmailAdapter"]
