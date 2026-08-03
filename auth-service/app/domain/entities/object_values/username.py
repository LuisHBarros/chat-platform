from app.domain.exceptions import ValidationError


class Username:
    def __init__ (self, value:str):
        value = value.strip()

        if len(value) < 3:
            raise ValidationError("Username must have at least 3 characters.")
        if len(value) >= 50:
            raise ValidationError("Username must have at most 50 characters")

        self._value = value

    @property
    def value(self) -> str:
        return self._value

    def __eq__(self, other):
        return isinstance(other, Username) and self.value == other.value

    def __hash__(self):
        return hash(self.value)
