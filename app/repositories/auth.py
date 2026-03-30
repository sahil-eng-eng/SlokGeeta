"""Auth repository — data access for User and RefreshToken."""

from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, RefreshToken


class AuthRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.google_id == google_id))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        await self.db.execute(
            update(User).where(User.id == user_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_by_id(user_id)

    async def verify_user(self, email: str) -> None:
        await self.db.execute(
            update(User).where(User.email == email).values(is_verified=True)
        )
        await self.db.flush()

    # ── Refresh tokens ──────────────────────────────────────────

    async def create_refresh_token(self, token: RefreshToken) -> RefreshToken:
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token_hash: str) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(is_revoked=True)
        )
        await self.db.flush()

    async def revoke_all_user_tokens(self, user_id: str) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(is_revoked=True)
        )
        await self.db.flush()

    async def search_users(self, query: str, limit: int = 20) -> list[User]:
        result = await self.db.execute(
            select(User)
            .where(
                User.is_active == True,  # noqa: E712
                (User.username.ilike(f"%{query}%"))
                | (User.full_name.ilike(f"%{query}%")),
            )
            .limit(limit)
        )
        return list(result.scalars().all())
