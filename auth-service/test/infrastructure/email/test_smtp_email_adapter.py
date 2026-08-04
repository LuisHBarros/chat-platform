from unittest.mock import MagicMock, patch

import pytest

from app.domain.entities.object_values import Email
from app.domain.exceptions import EmailDeliveryError
from app.domain.services.email_service import EmailService
from app.infrastructure.email.smtp_email_adapter import EmailAdapter, SMTPEmailAdapter


def test_smtp_email_adapter_implements_protocol():
    adapter = SMTPEmailAdapter()
    assert isinstance(adapter, EmailService)


def test_smtp_email_adapter_default_config(monkeypatch):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_PORT", raising=False)
    adapter = SMTPEmailAdapter()
    assert adapter.host == "localhost"
    assert adapter.port == 1025
    assert adapter.from_email == "noreply@discord-like.com"


def test_smtp_email_adapter_custom_config():
    adapter = SMTPEmailAdapter(
        host="mail.example.com",
        port=587,
        username="user",
        password="password",
        from_email="auth@example.com",
        from_name="Custom Auth",
        use_tls=True,
    )
    assert adapter.host == "mail.example.com"
    assert adapter.port == 587
    assert adapter.username == "user"
    assert adapter.password == "password"
    assert adapter.from_email == "auth@example.com"
    assert adapter.from_name == "Custom Auth"
    assert adapter.use_tls is True


@pytest.mark.asyncio
async def test_send_email_success():
    adapter = SMTPEmailAdapter(host="localhost", port=1025)

    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp

        recipient = Email("test@example.com")
        await adapter.send_email(
            recipient=recipient,
            subject="Test Subject",
            body_html="<p>Test Body</p>",
            body_text="Test Body",
        )

        mock_smtp_cls.assert_called_once_with("localhost", 1025, timeout=10.0)
        mock_smtp.send_message.assert_called_once()
        sent_msg = mock_smtp.send_message.call_args[0][0]
        assert sent_msg["To"] == "test@example.com"
        assert sent_msg["Subject"] == "Test Subject"
        assert "Discord-Like Auth <noreply@discord-like.com>" in sent_msg["From"]


@pytest.mark.asyncio
async def test_send_email_with_tls_and_auth():
    adapter = SMTPEmailAdapter(
        host="smtp.example.com",
        port=587,
        username="smtp_user",
        password="smtp_password",
        use_tls=True,
    )

    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp

        await adapter.send_email(
            recipient="user@example.com",
            subject="TLS Test",
            body_html="<p>TLS Test</p>",
        )

        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("smtp_user", "smtp_password")
        mock_smtp.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_email_with_ssl():
    adapter = SMTPEmailAdapter(
        host="smtp.example.com",
        port=465,
        use_ssl=True,
    )

    with patch("smtplib.SMTP_SSL") as mock_smtp_ssl_cls:
        mock_smtp = MagicMock()
        mock_smtp_ssl_cls.return_value.__enter__.return_value = mock_smtp

        await adapter.send_email(
            recipient="user@example.com",
            subject="SSL Test",
            body_html="<p>SSL Test</p>",
        )

        mock_smtp_ssl_cls.assert_called_once_with("smtp.example.com", 465, timeout=10.0)
        mock_smtp.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_verification_email():
    adapter = SMTPEmailAdapter(frontend_url="http://app.example.com")

    with patch.object(adapter, "send_email") as mock_send_email:
        await adapter.send_verification_email(
            recipient=Email("verify@example.com"),
            token="verify_token_123",
        )

        mock_send_email.assert_called_once()
        kwargs = mock_send_email.call_args.kwargs
        assert kwargs["recipient"] == Email("verify@example.com")
        assert "Verify Your Account" in kwargs["subject"]
        assert "http://app.example.com/verify-email?token=verify_token_123" in kwargs["body_html"]
        assert "http://app.example.com/verify-email?token=verify_token_123" in kwargs["body_text"]


@pytest.mark.asyncio
async def test_send_password_reset_email():
    adapter = SMTPEmailAdapter(frontend_url="http://app.example.com")

    with patch.object(adapter, "send_email") as mock_send_email:
        await adapter.send_password_reset_email(
            recipient="reset@example.com",
            token="reset_token_456",
        )

        mock_send_email.assert_called_once()
        kwargs = mock_send_email.call_args.kwargs
        assert kwargs["recipient"] == "reset@example.com"
        assert "Reset Your Password" in kwargs["subject"]
        assert "http://app.example.com/reset-password?token=reset_token_456" in kwargs["body_html"]
        assert "http://app.example.com/reset-password?token=reset_token_456" in kwargs["body_text"]


@pytest.mark.asyncio
async def test_send_email_smtp_error_raises_email_delivery_error():
    adapter = SMTPEmailAdapter()

    with patch("smtplib.SMTP", side_effect=Exception("Connection refused")):
        with pytest.raises(EmailDeliveryError, match="Failed to send email via SMTP"):
            await adapter.send_email(
                recipient="error@example.com",
                subject="Error Test",
                body_html="<p>Error</p>",
            )


def test_email_adapter_alias():
    assert EmailAdapter is SMTPEmailAdapter
