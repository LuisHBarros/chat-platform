import pytest
from app.domain.entities.object_values import Email
from app.domain.exceptions import ValidationError


def test_valid_email_creation_and_normalization():
    email = Email("  TEST.User@Example.COM ")
    assert email.value == "test.user@example.com"


def test_invalid_email_raises_validation_error():
    with pytest.raises(ValidationError, match="Invalid email"):
        Email("invalid-email-string")

    with pytest.raises(ValidationError):
        Email("user@domain")

    with pytest.raises(ValidationError):
        Email("@example.com")


def test_email_equality_and_hashing():
    email1 = Email("user@example.com")
    email2 = Email("USER@EXAMPLE.COM")
    email3 = Email("other@example.com")

    assert email1 == email2
    assert email1 != email3
    assert hash(email1) == hash(email2)
