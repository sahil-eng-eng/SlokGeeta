"""Book endpoint tests."""

import pytest
from unittest.mock import patch, AsyncMock
from app.schemas.books import BookResponse, BookListResponse


_MOCK_BOOK = BookResponse(
    id="book-1",
    owner_id="test-user-id",
    title="Bhagavad Gita",
    description="A spiritual text",
    cover_image_url=None,
    category="spiritual",
    tags=["vedas"],
    source=None,
    author_name="Vyasa",
    visibility="private",
    created_at="2024-01-01T00:00:00",
    updated_at="2024-01-01T00:00:00",
)


@pytest.mark.asyncio
async def test_create_book(client):
    with patch(
        "app.services.books.BookService.create_book",
        new_callable=AsyncMock,
        return_value=_MOCK_BOOK,
    ):
        resp = await client.post(
            "/api/v1/books",
            json={
                "title": "Bhagavad Gita",
                "description": "A spiritual text",
                "category": "spiritual",
                "tags": ["vedas"],
                "author_name": "Vyasa",
                "visibility": "private",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status_code"] == 201
        assert body["data"]["title"] == "Bhagavad Gita"


@pytest.mark.asyncio
async def test_list_my_books(client):
    mock_list = BookListResponse(
        items=[_MOCK_BOOK],
        next_cursor=None,
        has_more=False,
    )
    with patch(
        "app.services.books.BookService.list_my_books",
        new_callable=AsyncMock,
        return_value=mock_list,
    ):
        resp = await client.get("/api/v1/books/me")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]["items"]) == 1


@pytest.mark.asyncio
async def test_get_book(client):
    with patch(
        "app.services.books.BookService.get_book",
        new_callable=AsyncMock,
        return_value=_MOCK_BOOK,
    ):
        resp = await client.get("/api/v1/books/book-1")
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["id"] == "book-1"


@pytest.mark.asyncio
async def test_delete_book(client):
    with patch(
        "app.services.books.BookService.delete_book",
        new_callable=AsyncMock,
    ):
        resp = await client.delete("/api/v1/books/book-1")
        assert resp.status_code == 200
        body = resp.json()
        assert body["message"] == "Book deleted"
