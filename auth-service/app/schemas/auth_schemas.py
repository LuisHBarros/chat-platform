from pydantic import BaseModel, Field

try:
    from pydantic import EmailStr
except ImportError:
    EmailStr = str

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class LoginRequest(BaseModel):
    identity: str  # Email or username
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str | None = None
    email: str
    username: str
    is_active: bool = True
    is_verified: bool = False

class RefreshRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    access_token: str
    refresh_token: str

class VerifyTokenRequest(BaseModel):
    token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)

class ResendVerificationRequest(BaseModel):
    email: EmailStr
