"""Auth routes — register, login, verify, forgot/reset password, profile."""

from fastapi import APIRouter, Depends, Request, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.responses import ApiResponse
from app.services.auth import AuthService
from app.schemas.auth import (
    RegisterRequest,
    VerifyOTPRequest,
    LoginRequest,
    GoogleAuthRequest,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    UpdateProfileRequest,
    UserResponse,
    TokenResponse,
)
from app.constants.messages import AUTH_MESSAGES
from app.utils.supabase import upload_file

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=ApiResponse)
@limiter.limit("5/minute")
async def register(
    request: Request,
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):

    service = AuthService(db)
    print(f"Data = {data}")
    result = await service.register(data)
    return ApiResponse(
        status_code=201,
        message=result["message"],
        data=result["user"],
    )


@router.post("/resend-otp", response_model=ApiResponse)
@limiter.limit("3/minute")
async def resend_otp(
    request: Request,
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    result = await service.resend_otp(data.email)
    return ApiResponse(status_code=200, message=result["message"])


@router.post("/verify-email", response_model=ApiResponse)
async def verify_email(
    data: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    result = await service.verify_email(data.token)
    return ApiResponse(status_code=200, message=result["message"])


@router.post("/login", response_model=ApiResponse[TokenResponse])
@limiter.limit("10/minute")
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    device_info = request.headers.get("User-Agent", "")
    service = AuthService(db)
    result = await service.login(data, device_info)
    return ApiResponse(
        status_code=200,
        message=AUTH_MESSAGES["LOGIN_SUCCESS"],
        data=result,
    )


@router.post("/google", response_model=ApiResponse[TokenResponse])
async def google_auth(
    request: Request,
    data: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    device_info = request.headers.get("User-Agent", "")
    service = AuthService(db)
    result = await service.google_auth(data, device_info)
    return ApiResponse(
        status_code=200,
        message=AUTH_MESSAGES["GOOGLE_AUTH_SUCCESS"],
        data=result,
    )


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    result = await service.refresh(data.refresh_token)
    return ApiResponse(
        status_code=200,
        message=AUTH_MESSAGES["TOKEN_REFRESHED"],
        data=result,
    )


@router.post("/logout", response_model=ApiResponse)
async def logout(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.logout(data.refresh_token)
    return ApiResponse(
        status_code=200,
        message=AUTH_MESSAGES["LOGGED_OUT"],
    )


@router.post("/logout-all", response_model=ApiResponse)
async def logout_all(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = AuthService(db)
    await service.logout_all(current_user.id)
    return ApiResponse(
        status_code=200,
        message=AUTH_MESSAGES["ALL_SESSIONS_LOGGED_OUT"],
    )


@router.post("/forgot-password", response_model=ApiResponse)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    result = await service.forgot_password(data.email)
    return ApiResponse(status_code=200, message=result["message"])


@router.post("/reset-password", response_model=ApiResponse)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    result = await service.reset_password(data.token, data.new_password)
    return ApiResponse(status_code=200, message=result["message"])


@router.post("/change-password", response_model=ApiResponse)
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = AuthService(db)
    result = await service.change_password(
        current_user.id, data.current_password, data.new_password
    )
    return ApiResponse(status_code=200, message=result["message"])


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_me(current_user=Depends(get_current_user)):
    return ApiResponse(
        status_code=200,
        message=AUTH_MESSAGES["PROFILE_RETRIEVED"],
        data=UserResponse.model_validate(current_user),
    )


@router.patch("/me", response_model=ApiResponse[UserResponse])
async def update_profile(
    data: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = AuthService(db)
    result = await service.update_profile(current_user.id, data)
    return ApiResponse(
        status_code=200,
        message=AUTH_MESSAGES["PROFILE_UPDATED"],
        data=result,
    )


@router.post("/me/avatar", response_model=ApiResponse[UserResponse])
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    content = await file.read()
    ext = (
        file.filename.split(".")[-1] if file.filename else "png"
    )
    path = f"{current_user.id}/avatar.{ext}"
    url = await upload_file(
        "avatars", path, content, file.content_type or "image/png"
    )
    from app.repositories.auth import AuthRepository

    repo = AuthRepository(db)
    user = await repo.update_user(current_user.id, avatar_url=url)
    return ApiResponse(
        status_code=200,
        message=AUTH_MESSAGES["AVATAR_UPLOADED"],
        data=UserResponse.model_validate(user),
    )
