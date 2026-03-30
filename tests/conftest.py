"""Shared test fixtures for the ShlokVault test suite."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.dependencies import get_current_user, get_optional_user
from app.core.database import get_db
from app.models.user import User


# ── Fake user for auth-dependent tests ──────────────────────

def _make_test_user(**overrides) -> User:
    defaults = {
        "id": "test-user-id",
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "hashed_password": "fakehash",
        "avatar_url": None,
        "bio": None,
        "is_active": True,
        "is_verified": True,
        "auth_provider": "email",
        "google_id": None,
    }
    defaults.update(overrides)
    user = MagicMock(spec=User)
    for k, v in defaults.items():
        setattr(user, k, v)
    return user


@pytest.fixture
def test_user():
    return _make_test_user()


# ── Mock DB session ─────────────────────────────────────────

@pytest_asyncio.fixture
async def mock_db():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


# ── Override dependencies ────────────────────────────────────

@pytest_asyncio.fixture
async def client(mock_db, test_user):
    """HTTPX AsyncClient with overridden DB and auth deps."""

    async def _override_get_db():
        yield mock_db

    async def _override_get_current_user():
        return test_user

    async def _override_get_optional_user():
        return test_user

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    app.dependency_overrides[get_optional_user] = _override_get_optional_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def anon_client(mock_db):
    """HTTPX AsyncClient with no auth — for public endpoints."""

    async def _override_get_db():
        yield mock_db

    async def _override_get_optional_user():
        return None

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_optional_user] = _override_get_optional_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
