"""Integration tests for auth API endpoints (DEMO_MODE stubs)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    """POST /api/v1/auth/register returns user_id in demo mode."""
    body = {
        "phone": "+919876543210",
        "email": "test@test.com",
        "password": "Test@1234",
        "name": "Test",
        "company_name": "TestCo",
        "gstin": "27AABCT1234R1ZM",
    }

    response = await client.post("/api/v1/auth/register", json=body)

    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert data["user_id"]  # non-empty
    assert "message" in data


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    """POST /api/v1/auth/login returns access_token in demo mode."""
    body = {
        "phone_or_email": "test@test.com",
        "password": "Test@1234",
    }

    response = await client.post("/api/v1/auth/login", json=body)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["access_token"]  # non-empty
    assert "refresh_token" in data
    assert "user" in data


@pytest.mark.asyncio
async def test_verify_otp(client: AsyncClient):
    """POST /api/v1/auth/verify-otp returns 200 in demo mode."""
    body = {
        "phone": "+919876543210",
        "otp_code": "123456",
    }

    response = await client.post("/api/v1/auth/verify-otp", json=body)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_refresh(client: AsyncClient):
    """POST /api/v1/auth/refresh returns new access_token in demo mode."""
    body = {
        "refresh_token": "some_token",
    }

    response = await client.post("/api/v1/auth/refresh", json=body)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["access_token"]  # non-empty


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    """GET /api/v1/auth/me returns authenticated user info."""
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "name" in data
    assert "email" in data
    assert "phone" in data
    assert data["name"] == "Test User"
    assert data["email"] == "test@chainfactor.ai"
