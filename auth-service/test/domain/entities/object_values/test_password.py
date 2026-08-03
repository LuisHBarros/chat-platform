import pytest
from app.domain.entities.object_values import Password
from app.domain.exceptions import ValidationError


def test_valid_password_creation():
    pwd = Password("hashed_secret_123")
    assert pwd.hashed_value == "hashed_secret_123"


def test_empty_password_raises_error():
    with pytest.raises(ValidationError, match="cannot be empty"):
        Password("")


def test_password_equality_and_hashing():
    p1 = Password("hash123")
    p2 = Password("hash123")
    p3 = Password("hash456")

    assert p1 == p2
    assert p1 != p3
    assert hash(p1) == hash(p2)
