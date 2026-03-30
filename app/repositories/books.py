"""Book repository — data access for Book model."""

from typing import Optional
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.book import Book
from app.models.entity_permission import EntityPermission
from app.constants.enums import Visibility
from app.utils.pagination import decode_cursor


class BookRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, book: Book) -> Book:
        self.db.add(book)
        await self.db.flush()
        return book

    async def get_by_id(self, book_id: str) -> Optional[Book]:
        result = await self.db.execute(select(Book).where(Book.id == book_id))
        return result.scalar_one_or_none()

    async def update(self, book_id: str, **kwargs) -> Optional[Book]:
        await self.db.execute(
            update(Book).where(Book.id == book_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_by_id(book_id)

    async def delete(self, book_id: str) -> None:
        await self.db.execute(delete(Book).where(Book.id == book_id))
        await self.db.flush()

    async def list_by_owner(
        self, owner_id: str, cursor: Optional[str] = None, limit: int = 20
    ) -> list[Book]:
        query = (
            select(Book)
            .where(Book.owner_id == owner_id)
            .order_by(Book.created_at.desc(), Book.id.desc())
        )
        if cursor:
            decoded = decode_cursor(cursor)
            if decoded:
                ts, cid = decoded
                query = query.where(
                    or_(
                        Book.created_at < ts,
                        and_(Book.created_at == ts, Book.id < cid),
                    )
                )
        query = query.limit(limit + 1)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_public(
        self,
        cursor: Optional[str] = None,
        limit: int = 20,
        category: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> list[Book]:
        query = (
            select(Book)
            .where(Book.visibility == Visibility.PUBLIC)
            .order_by(Book.created_at.desc(), Book.id.desc())
        )
        if category:
            query = query.where(Book.category == category)
        if owner_id:
            query = query.where(Book.owner_id == owner_id)
        if cursor:
            decoded = decode_cursor(cursor)
            if decoded:
                ts, cid = decoded
                query = query.where(
                    or_(
                        Book.created_at < ts,
                        and_(Book.created_at == ts, Book.id < cid),
                    )
                )
        query = query.limit(limit + 1)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_shared_with_user(self, user_id: str) -> list[Book]:
        """Return books explicitly shared (non-structural) with user_id."""
        result = await self.db.execute(
            select(Book)
            .join(EntityPermission, EntityPermission.entity_id == Book.id)
            .where(
                EntityPermission.user_id == user_id,
                EntityPermission.entity_type == "book",
                EntityPermission.is_structural == False,  # noqa: E712
                EntityPermission.is_hidden == False,  # noqa: E712
            )
            .order_by(Book.created_at.desc())
        )
        return list(result.scalars().all())
