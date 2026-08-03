from app.domain.exceptions import ValidationError


class Password:
    def __init__(self, hashed_value: str):
        if not hashed_value:
            raise ValidationError("Password hash cannot be empty")

        self._hashed_value = hashed_value

    @property
    def hashed_value(self):
        return self._hashed_value

    def __eq__(self, other) -> bool:
        return isinstance(other, Password) and other.hashed_value == self.hashed_value

    def __hash__(self):
        return hash(self.hashed_value)
