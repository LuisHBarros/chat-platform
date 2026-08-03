from datetime import UTC, datetime

from app.domain.entities import Email, Password, User, Username


def test_user_creation():
    now = datetime.now(UTC)
    email = Email("user@example.com")
    username = Username("user123")
    password = Password("hashed_password")

    user = User.create(email, username, password, now)

    assert user.id is not None
    assert user.email == email
    assert user.username == username
    assert user.password == password
    assert user.is_active is True
    assert user.is_verified is False
    assert user.is_superuser is False
    assert user.can_authenticate() is False  # not verified yet


def test_user_verify_and_authenticate():
    now = datetime.now(UTC)
    user = User.create(Email("user@example.com"), Username("user123"), Password("hash"), now)

    verified_user = user.verify(now)
    assert verified_user.is_verified is True
    assert verified_user.can_authenticate() is True

    # Re-verifying should return the same object
    reverified = verified_user.verify(now)
    assert reverified == verified_user


def test_user_deactivate_and_activate():
    now = datetime.now(UTC)
    user = User.create(Email("user@example.com"), Username("user123"), Password("hash"), now).verify(now)

    deactivated = user.deactivate(now)
    assert deactivated.is_active is False
    assert deactivated.can_authenticate() is False

    activated = deactivated.activate(now)
    assert activated.is_active is True
    assert activated.can_authenticate() is True


def test_user_change_password():
    now = datetime.now(UTC)
    user = User.create(Email("user@example.com"), Username("user123"), Password("hash1"), now)

    new_password = Password("hash2")
    updated_user = user.change_password(new_password, now)

    assert updated_user.password == new_password
    assert updated_user.id == user.id
