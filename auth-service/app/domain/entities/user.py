from datetime import datetime
from uuid import UUID
from dataclasses import dataclass

@dataclass
class User:
    id: UUID
    email: str
    username: str
    password_hash: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
