class DomainError(Exception):
    """Base for all domain errors."""


class AuthenticationError(DomainError):
    """Invalid credentials or auth failure."""


class UserNotActiveError(DomainError):
    """User account is not active."""


class UserNotVerifiedError(DomainError):
    """User account is not verified."""


class UserAlreadyExistsError(DomainError):
    """User with the given email or username already exists."""


class ValidationError(DomainError):
    """Invalid value objects or inputs."""
