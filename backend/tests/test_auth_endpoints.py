"""Integration tests for auth API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    """POST /api/v1/auth/register returns user_id."""
    body = {
        "phone": "+919999999999",
        "email": "newuser@test.com",
        "password": "Test@1234",
        "name": "New User",
        "company_name": "NewCo",
        "gstin": "29AABCN5678R1ZX",
    }

    response = await client.post("/api/v1/auth/register", json=body)

    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert data["user_id"]  # non-empty
    assert "message" in data


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    """Register a new user, then login with those credentials."""
    # Register
    reg_body = {
        "phone": "+919888888888",
        "email": "logintest@test.com",
        "password": "Login@1234",
        "name": "Login Test",
        "company_name": "LoginCo",
        "gstin": "27AABCL5678R1ZX",
    }
    reg_resp = await client.post("/api/v1/auth/register", json=reg_body)
    assert reg_resp.status_code == 200

    # Login with same credentials
    login_body = {
        "phone_or_email": "logintest@test.com",
        "password": "Login@1234",
    }
    response = await client.post("/api/v1/auth/login", json=login_body)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["access_token"]  # non-empty
    assert "refresh_token" in data
    assert "user" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Login with wrong password returns 401."""
    # Register first
    reg_body = {
        "phone": "+919777777777",
        "email": "wrongpwd@test.com",
        "password": "Correct@1234",
        "name": "Wrong Pwd",
        "company_name": "WrongCo",
        "gstin": "29AABCW9999R1ZX",
    }
    await client.post("/api/v1/auth/register", json=reg_body)

    # Login with wrong password
    login_body = {
        "phone_or_email": "wrongpwd@test.com",
        "password": "Wrong@1234",
    }
    response = await client.post("/api/v1/auth/login", json=login_body)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_verify_otp(client: AsyncClient):
    """POST /api/v1/auth/verify-otp returns tokens for existing user."""
    body = {
        "phone": "+919876543210",
        "otp_code": "123456",
    }

    response = await client.post("/api/v1/auth/verify-otp", json=body)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_register_and_refresh(client: AsyncClient):
    """Register, login, then refresh the token."""
    # Register
    reg_body = {
        "phone": "+919666666666",
        "email": "refresh@test.com",
        "password": "Refresh@1234",
        "name": "Refresh Test",
        "company_name": "RefreshCo",
        "gstin": "27AABCR9999R1ZX",
    }
    await client.post("/api/v1/auth/register", json=reg_body)

    # Login to get tokens
    login_body = {
        "phone_or_email": "refresh@test.com",
        "password": "Refresh@1234",
    }
    login_resp = await client.post("/api/v1/auth/login", json=login_body)
    assert login_resp.status_code == 200
    refresh_token = login_resp.json()["refresh_token"]

    # Refresh
    refresh_body = {"refresh_token": refresh_token}
    response = await client.post("/api/v1/auth/refresh", json=refresh_body)

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
