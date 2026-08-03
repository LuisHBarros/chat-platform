import re

from app.domain.exceptions import ValidationError


class Email:
    EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self, value:str):
        value = value.strip().lower()

        if not self.EMAIL_REGEX.match(value):
            raise ValidationError("Invalid email")
        self._value = value

    @property
    def value(self):
        return self._value

    def __eq__(self, other) -> bool:
        return isinstance(other, Email) and other.value == self.value

    def __hash__(self):
        return hash(self.value)
