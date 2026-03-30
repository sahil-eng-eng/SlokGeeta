"""Auth endpoint tests."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.schemas.auth import UserResponse


@pytest.mark.asyncio
async def test_get_me(client, test_user):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status_code"] == 200
    assert body["message"] == "User profile retrieved"
    assert body["data"]["id"] == test_user.id


@pytest.mark.asyncio
async def test_verify_email_invalid_token(client):
    with patch(
        "app.services.auth.AuthService.verify_email",
        new_callable=AsyncMock,
    ) as mock_verify:
        from app.exceptions.auth import InvalidToken

        mock_verify.side_effect = InvalidToken()
        resp = await client.post(
            "/api/v1/auth/verify-email",
            json={"token": "bad-token"},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_success(client):
    mock_user_resp = UserResponse(
        id="test-user-id",
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        is_verified=True,
        auth_provider="email",
        created_at="2024-01-01T00:00:00",
    )
    mock_token = MagicMock()
    mock_token.model_dump.return_value = {
        "access_token": "fake-access",
        "refresh_token": "fake-refresh",
        "token_type": "bearer",
        "user": mock_user_resp.model_dump(),
    }

    with patch(
        "app.services.auth.AuthService.login",
        new_callable=AsyncMock,
        return_value=mock_token,
    ):
        resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["message"] == "Login successful"
