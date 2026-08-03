import pytest
from app.domain.entities.object_values import Username
from app.domain.exceptions import ValidationError


def test_valid_username_creation():
    username = Username("  john_doe  ")
    assert username.value == "john_doe"


def test_username_too_short():
    with pytest.raises(ValidationError, match="at least 3 characters"):
        Username("ab")


def test_username_too_long():
    with pytest.raises(ValidationError, match="at most 50 characters"):
        Username("a" * 51)


def test_username_equality_and_hashing():
    u1 = Username("john_doe")
    u2 = Username("john_doe")
    u3 = Username("jane_doe")

    assert u1 == u2
    assert u1 != u3
    assert hash(u1) == hash(u2)
