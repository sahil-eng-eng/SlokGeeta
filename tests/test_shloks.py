"""Shlok endpoint tests."""

import pytest
from unittest.mock import patch, AsyncMock
from app.schemas.shloks import ShlokResponse, ShlokListResponse


_MOCK_SHLOK = ShlokResponse(
    id="shlok-1",
    book_id="book-1",
    owner_id="test-user-id",
    content="dharma-ksetre kuru-ksetre",
    chapter_number=1,
    verse_number=1,
    tags=["gita"],
    audio_url=None,
    visibility="private",
    scheduled_at=None,
    view_count=0,
    created_at="2024-01-01T00:00:00",
    updated_at="2024-01-01T00:00:00",
)


@pytest.mark.asyncio
async def test_create_shlok(client):
    with patch(
        "app.services.shloks.ShlokService.create_shlok",
        new_callable=AsyncMock,
        return_value=_MOCK_SHLOK,
    ):
        resp = await client.post(
            "/api/v1/shloks",
            json={
                "book_id": "book-1",
                "content": "dharma-ksetre kuru-ksetre",
                "chapter_number": 1,
                "verse_number": 1,
                "tags": ["gita"],
                "visibility": "private",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status_code"] == 201
        assert body["data"]["content"] == "dharma-ksetre kuru-ksetre"


@pytest.mark.asyncio
async def test_list_shloks_by_book(client):
    mock_list = ShlokListResponse(
        items=[_MOCK_SHLOK],
        next_cursor=None,
        has_more=False,
    )
    with patch(
        "app.services.shloks.ShlokService.list_by_book",
        new_callable=AsyncMock,
        return_value=mock_list,
    ):
        resp = await client.get("/api/v1/shloks/book/book-1")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]["items"]) == 1


@pytest.mark.asyncio
async def test_get_shlok(client):
    with patch(
        "app.services.shloks.ShlokService.get_shlok",
        new_callable=AsyncMock,
        return_value=_MOCK_SHLOK,
    ):
        resp = await client.get("/api/v1/shloks/shlok-1")
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["id"] == "shlok-1"


@pytest.mark.asyncio
async def test_delete_shlok(client):
    with patch(
        "app.services.shloks.ShlokService.delete_shlok",
        new_callable=AsyncMock,
    ):
        resp = await client.delete("/api/v1/shloks/shlok-1")
        assert resp.status_code == 200
        body = resp.json()
        assert body["message"] == "Shlok deleted"
