"""Public discovery routes.

GET /discover/books   — paginated list of all books (public)
GET /discover/shloks  — paginated list of all shloks (public)
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.book import Book
from app.models.shlok import Shlok
from app.core.responses import ApiResponse

router = APIRouter(prefix="/discover", tags=["discover"])

_DEFAULT_PAGE_SIZE = 20
_MAX_PAGE_SIZE = 100


@router.get("/books", response_model=None)
async def discover_books(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, le=_MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    count_q = await db.execute(select(func.count()).select_from(Book))
    total = count_q.scalar_one()
    result = await db.execute(select(Book).offset(offset).limit(page_size).order_by(Book.created_at.desc()))
    books = result.scalars().all()
    return ApiResponse(
        status_code=200,
        data={
            "items": [
                {
                    "id": b.id,
                    "title": b.title,
                    "description": b.description,
                    "owner_id": b.owner_id,
                    "author_name": b.author_name,
                    "cover_image_url": b.cover_image_url,
                    "category": b.category,
                    "created_at": b.created_at.isoformat() if b.created_at else None,
                }
                for b in books
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        message="Books retrieved",
    )


@router.get("/shloks", response_model=None)
async def discover_shloks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, le=_MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    count_q = await db.execute(select(func.count()).select_from(Shlok))
    total = count_q.scalar_one()
    result = await db.execute(
        select(Shlok).offset(offset).limit(page_size).order_by(Shlok.created_at.desc())
    )
    shloks = result.scalars().all()
    return ApiResponse(
        status_code=200,
        data={
            "items": [
                {
                    "id": s.id,
                    "content": s.content,
                    "book_id": s.book_id,
                    "owner_id": s.owner_id,
                    "chapter_number": s.chapter_number,
                    "verse_number": s.verse_number,
                    "tags": s.tags,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
                for s in shloks
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        message="Shloks retrieved",
    )
