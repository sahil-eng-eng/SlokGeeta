"""Book routes — CRUD, cover upload, listing."""

from fastapi import APIRouter, Depends, UploadFile, File, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db, AsyncSessionLocal
from app.core.dependencies import get_current_user, get_optional_user
from app.core.responses import ApiResponse
from app.services.books import BookService
from app.schemas.books import (
    CreateBookRequest,
    UpdateBookRequest,
    BookResponse,
    BookListResponse,
)
from app.constants.messages import BOOK_MESSAGES

router = APIRouter(prefix="/books", tags=["Books"])


@router.post("", response_model=ApiResponse[BookResponse])
async def create_book(
    data: CreateBookRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = BookService(db)
    result = await service.create_book(current_user.id, data)
    return ApiResponse(
        status_code=201,
        message=BOOK_MESSAGES["CREATED"],
        data=result,
    )


@router.get("/shared-with-me", response_model=ApiResponse[BookListResponse])
async def list_shared_with_me(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = BookService(db)
    result = await service.list_shared_with_me(current_user.id)
    return ApiResponse(
        status_code=200,
        message=BOOK_MESSAGES["LIST_RETRIEVED"],
        data=result,
    )


@router.get("/me", response_model=ApiResponse[BookListResponse])
async def list_my_books(
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = BookService(db)
    result = await service.list_my_books(current_user.id, cursor, limit)
    return ApiResponse(
        status_code=200,
        message=BOOK_MESSAGES["LIST_RETRIEVED"],
        data=result,
    )


@router.get("/public", response_model=ApiResponse[BookListResponse])
async def list_public_books(
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    owner_id: Optional[str] = Query(None),
):
    async with AsyncSessionLocal() as db:
        service = BookService(db)
        result = await service.list_public_books(
            cursor, limit, category, owner_id
        )
        return ApiResponse(
            status_code=200,
            message=BOOK_MESSAGES["LIST_RETRIEVED"],
            data=result,
        )


@router.get("/{book_id}", response_model=ApiResponse[BookResponse])
async def get_book(
    book_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    service = BookService(db)
    user_id = current_user.id if current_user else None
    result = await service.get_book(book_id, user_id)
    return ApiResponse(
        status_code=200,
        message=BOOK_MESSAGES["RETRIEVED"],
        data=result,
    )


@router.patch("/{book_id}", response_model=ApiResponse[BookResponse])
async def update_book(
    book_id: str,
    data: UpdateBookRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = BookService(db)
    result = await service.update_book(book_id, current_user.id, data)
    return ApiResponse(
        status_code=200,
        message=BOOK_MESSAGES["UPDATED"],
        data=result,
    )


@router.delete("/{book_id}", response_model=ApiResponse)
async def delete_book(
    book_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = BookService(db)
    await service.delete_book(book_id, current_user.id)
    return ApiResponse(
        status_code=200,
        message=BOOK_MESSAGES["DELETED"],
    )


@router.post(
    "/{book_id}/cover", response_model=ApiResponse[BookResponse]
)
async def upload_cover(
    book_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    content = await file.read()
    ext = file.filename.split(".")[-1] if file.filename else "png"
    service = BookService(db)
    result = await service.upload_cover(
        book_id,
        current_user.id,
        content,
        file.content_type or "image/png",
        ext,
    )
    return ApiResponse(
        status_code=200,
        message=BOOK_MESSAGES["COVER_UPLOADED"],
        data=result,
    )
