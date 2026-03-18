"""Auth API stub endpoints. Returns hardcoded responses matching wireframes.md contract."""

from fastapi import APIRouter

from app.schemas.auth import (
    AuthTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    UserResponse,
    VerifyOTPRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])

STUB_USER = UserResponse(
    id="usr_stub_001",
    name="Manoj RS",
    email="manoj@acmetech.in",
    phone="+919876543210",
)


@router.post("/register", response_model=RegisterResponse)
async def register(body: RegisterRequest):
    return RegisterResponse(user_id="usr_stub_001", message="OTP sent")


@router.post("/login", response_model=AuthTokenResponse)
async def login(body: LoginRequest):
    return AuthTokenResponse(
        access_token="stub_access_token_jwt",
        refresh_token="stub_refresh_token",
        user=STUB_USER,
    )


@router.post("/verify-otp", response_model=AuthTokenResponse)
async def verify_otp(body: VerifyOTPRequest):
    return AuthTokenResponse(
        access_token="stub_access_token_jwt",
        refresh_token="stub_refresh_token",
        user=STUB_USER,
    )


@router.post("/refresh", response_model=AuthTokenResponse)
async def refresh(body: RefreshRequest):
    return AuthTokenResponse(
        access_token="stub_access_token_jwt_refreshed",
        refresh_token="stub_refresh_token_new",
        user=STUB_USER,
    )
