"""Auth service — business logic for registration, login, tokens, profile."""

import hashlib
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.auth import AuthRepository
from app.models.user import User, RefreshToken
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    GoogleAuthRequest,
    UserResponse,
    TokenResponse,
    UpdateProfileRequest,
)
from app.exceptions.auth import (
    EmailAlreadyExistsException,
    UsernameAlreadyExistsException,
    InvalidCredentialsException,
    AccountNotVerifiedException,
    InvalidTokenException,
    UserNotFoundException,
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_otp_token,
    generate_reset_token,
)
from app.constants.enums import AuthProvider
from app.constants.messages import AUTH_MESSAGES
from app.core.config import get_settings

settings = get_settings()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repo = AuthRepository(db)

    async def register(self, data: RegisterRequest) -> dict:
        if await self.repo.get_by_email(data.email):
            print("----")
            raise EmailAlreadyExistsException()
        if await self.repo.get_by_username(data.username):
            print("))))")
            raise UsernameAlreadyExistsException()
        print("+++++++++++")
        user = User(
            email=data.email,
            username=data.username,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            auth_provider=AuthProvider.EMAIL,
        )
        user = await self.repo.create(user)
        otp_token = generate_otp_token(data.email)
        print(f"OTP - TOKEN {otp_token}")
        from app.tasks.email_tasks import send_otp_email

        send_otp_email.delay(data.email, user.username, otp_token)

        return {
            "user": UserResponse.model_validate(user),
            "message": AUTH_MESSAGES["REGISTRATION_SUCCESS"],
        }

    async def verify_email(self, token: str) -> dict:
        payload = decode_token(token)
        if not payload or payload.get("type") != "otp":
            raise InvalidTokenException()
        email = payload.get("sub")
        user = await self.repo.get_by_email(email)
        if not user:
            raise UserNotFoundException()
        await self.repo.verify_user(email)
        return {"message": AUTH_MESSAGES["EMAIL_VERIFIED"]}

    async def login(
        self, data: LoginRequest, device_info: str = None
    ) -> TokenResponse:
        user = await self.repo.get_by_email(data.email)
        if not user or not user.hashed_password:
            raise InvalidCredentialsException()
        if not verify_password(data.password, user.hashed_password):
            raise InvalidCredentialsException()
        if not user.is_verified:
            raise AccountNotVerifiedException()

        return await self._issue_tokens(user, data.remember_me, device_info)

    async def google_auth(
        self, data: GoogleAuthRequest, device_info: str = None
    ) -> TokenResponse:
        google_user = await self._verify_google_token(data.id_token)
        user = await self.repo.get_by_google_id(google_user["sub"])

        if not user:
            existing = await self.repo.get_by_email(google_user["email"])
            if existing:
                user = await self.repo.update_user(
                    existing.id,
                    google_id=google_user["sub"],
                    is_verified=True,
                )
            else:
                username = google_user["email"].split("@")[0]
                base_username = username
                counter = 1
                while await self.repo.get_by_username(username):
                    username = f"{base_username}{counter}"
                    counter += 1
                user = User(
                    email=google_user["email"],
                    username=username,
                    full_name=google_user.get("name", ""),
                    avatar_url=google_user.get("picture"),
                    auth_provider=AuthProvider.GOOGLE,
                    google_id=google_user["sub"],
                    is_verified=True,
                )
                user = await self.repo.create(user)

        return await self._issue_tokens(user, data.remember_me, device_info)

    async def refresh(self, refresh_token_str: str) -> TokenResponse:
        payload = decode_token(refresh_token_str)
        if not payload or payload.get("type") != "refresh":
            raise InvalidTokenException()

        token_hash = _hash_token(refresh_token_str)
        stored = await self.repo.get_refresh_token(token_hash)
        if not stored:
            raise InvalidTokenException()

        user = await self.repo.get_by_id(payload["sub"])
        if not user:
            raise UserNotFoundException()

        await self.repo.revoke_refresh_token(token_hash)
        return await self._issue_tokens(
            user, remember_me=False, device_info=stored.device_info
        )

    async def logout(self, refresh_token_str: str) -> None:
        token_hash = _hash_token(refresh_token_str)
        await self.repo.revoke_refresh_token(token_hash)

    async def logout_all(self, user_id: str) -> None:
        await self.repo.revoke_all_user_tokens(user_id)

    async def forgot_password(self, email: str) -> dict:
        user = await self.repo.get_by_email(email)
        if not user:
            return {"message": AUTH_MESSAGES["RESET_LINK_SENT"]}
        token = generate_reset_token(email)
        from app.tasks.email_tasks import send_password_reset_email

        send_password_reset_email.delay(
            email, user.username, token, settings.FRONTEND_URL
        )
        return {"message": AUTH_MESSAGES["RESET_LINK_SENT"]}

    async def reset_password(self, token: str, new_password: str) -> dict:
        payload = decode_token(token)
        if not payload or payload.get("type") != "reset":
            raise InvalidTokenException()
        email = payload.get("sub")
        user = await self.repo.get_by_email(email)
        if not user:
            raise UserNotFoundException()
        await self.repo.update_user(
            user.id, hashed_password=hash_password(new_password)
        )
        await self.repo.revoke_all_user_tokens(user.id)
        return {"message": AUTH_MESSAGES["PASSWORD_RESET_SUCCESS"]}

    async def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> dict:
        user = await self.repo.get_by_id(user_id)
        if not user or not user.hashed_password:
            raise UserNotFoundException()
        if not verify_password(current_password, user.hashed_password):
            raise InvalidCredentialsException()
        await self.repo.update_user(
            user_id, hashed_password=hash_password(new_password)
        )
        return {"message": AUTH_MESSAGES["PASSWORD_CHANGED"]}

    async def resend_otp(self, email: str) -> dict:
        user = await self.repo.get_by_email(email)
        if not user or user.is_verified:
            return {"message": AUTH_MESSAGES["OTP_RESENT"]}
        otp_token = generate_otp_token(email)
        from app.tasks.email_tasks import send_otp_email

        send_otp_email.delay(email, user.username, otp_token)
        return {"message": AUTH_MESSAGES["OTP_RESENT"]}

    async def update_profile(
        self, user_id: str, data: UpdateProfileRequest
    ) -> UserResponse:
        updates = data.model_dump(exclude_unset=True)
        if "username" in updates:
            existing = await self.repo.get_by_username(updates["username"])
            if existing and existing.id != user_id:
                raise UsernameAlreadyExistsException()
        user = await self.repo.update_user(user_id, **updates)
        return UserResponse.model_validate(user)

    async def get_me(self, user_id: str) -> UserResponse:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException()
        return UserResponse.model_validate(user)

    # ── Private ──────────────────────────────────────────────────

    async def _issue_tokens(
        self,
        user: User,
        remember_me: bool,
        device_info: str = None,
    ) -> TokenResponse:
        access = create_access_token({"sub": user.id})
        refresh = create_refresh_token(
            {"sub": user.id}, remember_me=remember_me
        )

        rt = RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(refresh),
            device_info=device_info,
        )
        await self.repo.create_refresh_token(rt)

        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            user=UserResponse.model_validate(user),
        )

    async def _verify_google_token(self, id_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
            )
            if resp.status_code != 200:
                raise InvalidTokenException()
            data = resp.json()
            if data.get("aud") != settings.GOOGLE_CLIENT_ID:
                raise InvalidTokenException()
            return data
