from datetime import datetime, timezone
from app.domain.entities.object_values import Email, Username, Password
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.password_hasher import PasswordHasher

class CreateNewUser:
    def __init__(self, user_repository: UserRepository, password_hasher: PasswordHasher):
        self.user_repository = user_repository
        self.password_hasher = password_hasher

    async def execute(self, email: Email, username: Username, password: str) -> User:
        now = datetime.now(timezone.utc)    
        existing_email = await self.user_repository.get_by_email(email)
        
        if existing_email is not None:
            raise ValueError("User with this email already exists")
        existing_username = await self.user_repository.get_by_username(username)
        
        if existing_username is not None:
            raise ValueError("User with this username already exists")
        
        if not password:
            raise ValueError("Password is required")

        hashed = self.password_hasher.hash(password)
        user = User.create(email, username, Password(hashed), now)
        
        return await self.user_repository.save(user)