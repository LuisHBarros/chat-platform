import os
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import (
    get_cache_repository,
    get_email_adapter,
    get_password_hasher,
    get_refresh_token_repository,
    get_token_service,
    get_user_repository,
    get_verification_token_repository,
)
from app.domain.entities.object_values import Email, Username
from app.domain.entities.verification_token import VerificationToken
from app.domain.exceptions import (
    AuthenticationError,
    EmailDeliveryError,
    UserAlreadyExistsError,
    UserNotActiveError,
    UserNotVerifiedError,
    ValidationError,
)
from app.domain.repositories import (
    CacheRepository,
    RefreshTokenRepository,
    UserRepository,
    VerificationTokenRepository,
)
from app.domain.services import (
    AuthenticateUser,
    CreateNewUser,
    LogoutUser,
    PasswordHasher,
    ResetPasswordWithToken,
    RotateRefreshToken,
    TokenService,
    VerifyUser,
    VerifyUserWithToken,
)
from app.infrastructure.email.smtp_email_adapter import SMTPEmailAdapter
from app.schemas.auth_schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyTokenRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

AUTO_VERIFY_DEV = os.getenv("AUTO_VERIFY_DEV", "true").lower() == "true"


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    payload: RegisterRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    verification_token_repo: VerificationTokenRepository = Depends(get_verification_token_repository),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    email_adapter: SMTPEmailAdapter = Depends(get_email_adapter),
):
    try:
        email_vo = Email(payload.email)
        username_vo = Username(payload.username)

        creator = CreateNewUser(user_repo, password_hasher)
        user = await creator.execute(email_vo, username_vo, payload.password)

        now = datetime.now(UTC)
        token_entity, token_str = VerificationToken.create(user.id, "email_verification", now)
        await verification_token_repo.save(token_entity)

        try:
            await email_adapter.send_verification_email(user.email, token_str)
        except EmailDeliveryError as exc:
            logger.warning("Failed to send verification email during registration: %s", exc)

        if AUTO_VERIFY_DEV:
            user = await VerifyUser(user_repo).execute(user)

        return UserResponse(
            id=str(user.id),
            email=user.email.value,
            username=user.username.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
        )
    except (UserAlreadyExistsError, ValidationError) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.post(
    "/verify",
    status_code=status.HTTP_200_OK,
    summary="Verify user account via token",
)
async def verify(
    payload: VerifyTokenRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    verification_token_repo: VerificationTokenRepository = Depends(get_verification_token_repository),
):
    try:
        service = VerifyUserWithToken(user_repo, verification_token_repo)
        await service.execute(payload.token)
        return {"message": "Account verified successfully"}
    except ValidationError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.post(
    "/resend-verification",
    status_code=status.HTTP_200_OK,
    summary="Resend email verification token",
)
async def resend_verification(
    payload: ResendVerificationRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    verification_token_repo: VerificationTokenRepository = Depends(get_verification_token_repository),
    email_adapter: SMTPEmailAdapter = Depends(get_email_adapter),
):
    try:
        user = await user_repo.get_by_email(Email(payload.email))
        if user and not user.is_verified:
            now = datetime.now(UTC)
            token_entity, token_str = VerificationToken.create(user.id, "email_verification", now)
            await verification_token_repo.save(token_entity)
            try:
                await email_adapter.send_verification_email(user.email, token_str)
            except EmailDeliveryError as exc:
                logger.warning("Failed to resend verification email: %s", exc)
    except Exception as exc:
        logger.warning("Error during resend-verification flow: %s", exc)

    return {"message": "If an unverified account with that email exists, a new verification link has been sent."}


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and return access/refresh tokens",
)
async def login(
    payload: LoginRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    token_service: TokenService = Depends(get_token_service),
):
    authenticator = AuthenticateUser(user_repo, password_hasher, refresh_token_repo, token_service)

    try:
        if "@" in payload.identity:
            email_vo = Email(payload.identity)
            auth_result = await authenticator.with_email_and_password(email_vo, payload.password)
        else:
            username_vo = Username(payload.identity)
            auth_result = await authenticator.with_username_and_password(username_vo, payload.password)

        return TokenResponse(
            access_token=auth_result.access_token,
            refresh_token=auth_result.refresh_token,
            token_type="bearer",
        )
    except UserNotVerifiedError as err:
        if AUTO_VERIFY_DEV:
            user = None
            if "@" in payload.identity:
                user = await user_repo.get_by_email(Email(payload.identity))
            else:
                user = await user_repo.get_by_username(Username(payload.identity))
            if user:
                await VerifyUser(user_repo).execute(user)
                if "@" in payload.identity:
                    auth_result = await authenticator.with_email_and_password(Email(payload.identity), payload.password)
                else:
                    auth_result = await authenticator.with_username_and_password(Username(payload.identity), payload.password)
                return TokenResponse(
                    access_token=auth_result.access_token,
                    refresh_token=auth_result.refresh_token,
                    token_type="bearer",
                )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err)) from err
    except UserNotActiveError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err)) from err
    except (AuthenticationError, ValidationError) as err:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(err)) from err


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate refresh token and issue new access token",
)
async def refresh(
    payload: RefreshRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
    token_service: TokenService = Depends(get_token_service),
    cache_repo: CacheRepository | None = Depends(get_cache_repository),
):
    try:
        rotator = RotateRefreshToken(cache_repo, refresh_token_repo, token_service, user_repo)
        auth_result = await rotator.execute(payload.refresh_token)
        return TokenResponse(
            access_token=auth_result.access_token,
            refresh_token=auth_result.refresh_token,
            token_type="bearer",
        )
    except (AuthenticationError, ValidationError) as err:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(err)) from err


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Revoke tokens and logout user",
)
async def logout(
    payload: LogoutRequest,
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
    token_service: TokenService = Depends(get_token_service),
    cache_repo: CacheRepository | None = Depends(get_cache_repository),
):
    try:
        payloads = []
        if payload.access_token:
            payloads.append(token_service.decode(payload.access_token))
        if payload.refresh_token:
            payloads.append(token_service.decode(payload.refresh_token))

        if cache_repo and payloads:
            logout_service = LogoutUser(cache_repo, refresh_token_repo)
            await logout_service.execute(*payloads)

        return {"message": "Successfully logged out"}
    except (AuthenticationError, ValidationError) as err:
        return {"message": f"Logout completed: {err}"}


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Request password reset token via email",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    verification_token_repo: VerificationTokenRepository = Depends(get_verification_token_repository),
    email_adapter: SMTPEmailAdapter = Depends(get_email_adapter),
):
    try:
        user = await user_repo.get_by_email(Email(payload.email))
        if user:
            now = datetime.now(UTC)
            token_entity, token_str = VerificationToken.create(user.id, "password_reset", now)
            await verification_token_repo.save(token_entity)
            await email_adapter.send_password_reset_email(user.email, token_str)
    except Exception as exc:
        logger.warning("Error during forgot-password flow: %s", exc)

    return {"message": "If an account with that email exists, a password reset link has been sent."}


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset password using reset token",
)
async def reset_password(
    payload: ResetPasswordRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    verification_token_repo: VerificationTokenRepository = Depends(get_verification_token_repository),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
):
    try:
        service = ResetPasswordWithToken(user_repo, verification_token_repo, password_hasher)
        await service.execute(payload.token, payload.new_password)
        return {"message": "Password updated successfully"}
    except ValidationError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
