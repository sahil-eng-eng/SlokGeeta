"""FastAPI dependencies for auth and optional auth."""

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.database import get_db
from app.core.security import decode_token
from app.exceptions.base import UnauthorizedException
from app.constants.messages import AUTH_MESSAGES
from app.models.user import User


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException(AUTH_MESSAGES["MISSING_AUTH_HEADER"])
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedException(AUTH_MESSAGES["INVALID_TOKEN"])
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(AUTH_MESSAGES["INVALID_TOKEN_PAYLOAD"])
    from app.repositories.auth import AuthRepository

    repo = AuthRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise UnauthorizedException(AUTH_MESSAGES["USER_NOT_FOUND"])
    if not user.is_active:
        raise UnauthorizedException(AUTH_MESSAGES["ACCOUNT_DEACTIVATED"])
    return user


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split(" ")[1]
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        from app.repositories.auth import AuthRepository

        repo = AuthRepository(db)
        user = await repo.get_by_id(user_id)
        return user if user and user.is_active else None
    except Exception:
        return None
