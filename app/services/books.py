"""Book service — business logic for CRUD, cover upload, listing."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.books import BookRepository
from app.models.book import Book
from app.schemas.books import (
    CreateBookRequest,
    UpdateBookRequest,
    BookResponse,
    BookListResponse,
)
from app.exceptions.books import BookNotFoundException, BookForbiddenException, BookCannotMakePrivateException
from app.constants.enums import Visibility, PermissionLevel, EntityType
from app.utils.pagination import encode_cursor


class BookService:
    def __init__(self, db: AsyncSession):
        self.repo = BookRepository(db)
        self.db = db

    async def create_book(
        self, owner_id: str, data: CreateBookRequest
    ) -> BookResponse:
        book = Book(owner_id=owner_id, **data.model_dump())
        book = await self.repo.create(book)
        return BookResponse.model_validate(book)

    async def get_book(
        self, book_id: str, user_id: Optional[str] = None
    ) -> BookResponse:
        book = await self.repo.get_by_id(book_id)
        if not book:
            raise BookNotFoundException()
        await self._check_read_access(book, user_id)
        return BookResponse.model_validate(book)

    async def update_book(
        self, book_id: str, user_id: str, data: UpdateBookRequest
    ) -> BookResponse:
        book = await self.repo.get_by_id(book_id)
        if not book:
            raise BookNotFoundException()
        await self._check_write_access(book, user_id)
        updates = data.model_dump(exclude_unset=True)
        # Block changing to private when any shloks or meanings are still shared
        if updates.get("visibility") == "private":
            from app.repositories.shloks import ShlokRepository
            from app.repositories.meanings import MeaningRepository
            from app.repositories.entity_permissions import EntityPermissionRepository
            shlok_repo = ShlokRepository(self.db)
            meaning_repo = MeaningRepository(self.db)
            perm_repo = EntityPermissionRepository(self.db)
            shlok_ids = await shlok_repo.get_all_ids_by_book(book_id)
            if shlok_ids and await perm_repo.has_active_permissions_for_any("shlok", shlok_ids):
                raise BookCannotMakePrivateException()
            # Gather all meaning IDs across every shlok
            all_meaning_ids: list[str] = []
            for sid in shlok_ids:
                all_meaning_ids.extend(await meaning_repo.get_all_ids_by_shlok(sid))
            if all_meaning_ids and await perm_repo.has_active_permissions_for_any("meaning", all_meaning_ids):
                raise BookCannotMakePrivateException()
        if updates:
            book = await self.repo.update(book_id, **updates)
        return BookResponse.model_validate(book)

    async def delete_book(self, book_id: str, user_id: str) -> None:
        book = await self.repo.get_by_id(book_id)
        if not book:
            raise BookNotFoundException()
        if book.owner_id != user_id:
            raise BookForbiddenException()
        await self.repo.delete(book_id)

    async def upload_cover(
        self,
        book_id: str,
        user_id: str,
        file_bytes: bytes,
        content_type: str,
        ext: str,
    ) -> BookResponse:
        book = await self.repo.get_by_id(book_id)
        if not book:
            raise BookNotFoundException()
        await self._check_write_access(book, user_id)
        from app.utils.supabase import upload_file

        path = f"{user_id}/{book_id}/cover.{ext}"
        url = await upload_file("book-covers", path, file_bytes, content_type)
        book = await self.repo.update(book_id, cover_image_url=url)
        return BookResponse.model_validate(book)

    async def list_my_books(
        self,
        user_id: str,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> BookListResponse:
        books = await self.repo.list_by_owner(user_id, cursor, limit)
        has_more = len(books) > limit
        items = books[:limit]
        next_cursor = (
            encode_cursor(items[-1].created_at, items[-1].id)
            if has_more
            else None
        )
        return BookListResponse(
            items=[BookResponse.model_validate(b) for b in items],
            next_cursor=next_cursor,
            has_more=has_more,
        )

    async def list_public_books(
        self,
        cursor: Optional[str] = None,
        limit: int = 20,
        category: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> BookListResponse:
        books = await self.repo.list_public(cursor, limit, category, owner_id)
        has_more = len(books) > limit
        items = books[:limit]
        next_cursor = (
            encode_cursor(items[-1].created_at, items[-1].id)
            if has_more and items
            else None
        )
        return BookListResponse(
            items=[BookResponse.model_validate(b) for b in items],
            next_cursor=next_cursor,
            has_more=has_more,
        )

    async def list_shared_with_me(self, user_id: str) -> BookListResponse:
        books = await self.repo.list_shared_with_user(user_id)
        return BookListResponse(
            items=[BookResponse.model_validate(b) for b in books],
            next_cursor=None,
            has_more=False,
        )

    async def _check_read_access(
        self, book: Book, user_id: Optional[str]
    ) -> None:
        if book.visibility == Visibility.PUBLIC:
            return
        if user_id and book.owner_id == user_id:
            return
        if user_id:
            # Check entity-permission table regardless of the book's own visibility;
            # a structural row means a child entity was shared with this user,
            # so they need navigation access to the book.
            from app.repositories.entity_permissions import EntityPermissionRepository
            perm_repo = EntityPermissionRepository(self.db)
            perm = await perm_repo.get(user_id, "book", book.id)
            if perm and not perm.is_hidden:
                return
        raise BookForbiddenException()

    async def _check_write_access(self, book: Book, user_id: str) -> None:
        if book.owner_id == user_id:
            return
        from app.repositories.entity_permissions import EntityPermissionRepository
        perm_repo = EntityPermissionRepository(self.db)
        perm = await perm_repo.get(user_id, "book", book.id)
        if (
            perm
            and not perm.is_hidden
            and not perm.is_structural
            and perm.permission_level == PermissionLevel.DIRECT_EDIT.value
        ):
            return
        raise BookForbiddenException()
