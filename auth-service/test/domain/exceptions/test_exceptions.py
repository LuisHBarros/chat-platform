from app.domain.exceptions import (
    AuthenticationError,
    DomainError,
    EmailDeliveryError,
    UserAlreadyExistsError,
    UserNotActiveError,
    UserNotVerifiedError,
    ValidationError,
)


def test_exception_inheritance():
    assert issubclass(AuthenticationError, DomainError)
    assert issubclass(EmailDeliveryError, DomainError)
    assert issubclass(UserAlreadyExistsError, DomainError)
    assert issubclass(UserNotActiveError, DomainError)
    assert issubclass(UserNotVerifiedError, DomainError)
    assert issubclass(ValidationError, DomainError)


def test_raise_domain_exceptions():
    try:
        raise AuthenticationError("Invalid password")
    except DomainError as err:
        assert str(err) == "Invalid password"

