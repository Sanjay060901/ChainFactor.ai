"""Auth API endpoints -- Cognito integration with DEMO_MODE fallback."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.modules.auth.cognito_service import CognitoError, cognito_service
from app.modules.auth.dependencies import get_current_user
from app.schemas.auth import (
    AuthTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    UserResponse,
    VerifyOTPRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# --- Stub data for DEMO_MODE ---
STUB_USER = UserResponse(
    id="usr_demo_001",
    name="Demo User",
    email="demo@chainfactor.ai",
    phone="+919876543210",
)
STUB_TOKENS = AuthTokenResponse(
    access_token="demo_access_token",
    refresh_token="demo_refresh_token",
    user=STUB_USER,
)


@router.post("/register", response_model=RegisterResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user via Cognito. Sends OTP to phone/email."""
    if settings.DEMO_MODE:
        return RegisterResponse(user_id="usr_demo_001", message="OTP sent (demo mode)")

    try:
        result = await cognito_service.register(
            email=body.email,
            phone=body.phone,
            password=body.password,
            name=body.name,
            company_name=body.company_name,
            gstin=body.gstin,
        )

        # Pre-create user record in DB (will be confirmed after OTP)
        user = User(
            cognito_sub=result["user_sub"],
            name=body.name,
            email=body.email,
            phone=body.phone,
            company_name=body.company_name,
            gstin=body.gstin,
        )
        db.add(user)
        await db.flush()

        return RegisterResponse(
            user_id=str(user.id),
            message="OTP sent to your email. Please verify to complete registration.",
        )
    except CognitoError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post("/login", response_model=AuthTokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email/phone + password. Returns JWT tokens."""
    if settings.DEMO_MODE:
        return STUB_TOKENS

    try:
        result = await cognito_service.login(
            username=body.phone_or_email,
            password=body.password,
        )

        # If challenge returned (e.g., MFA), return partial response
        if "challenge" in result:
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail=f"Challenge required: {result['challenge']}",
            )

        # Fetch user info from Cognito to build response
        user_info = await cognito_service.get_user(result["access_token"])

        # Find or create user in DB
        db_result = await db.execute(
            select(User).where(User.cognito_sub == user_info["sub"])
        )
        user = db_result.scalar_one_or_none()

        if not user:
            user = User(
                cognito_sub=user_info["sub"],
                name=user_info["name"],
                email=user_info["email"],
                phone=user_info["phone"],
                company_name=user_info["company_name"],
                gstin=user_info["gstin"],
            )
            db.add(user)
            await db.flush()

        return AuthTokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            user=UserResponse(
                id=str(user.id),
                name=user.name,
                email=user.email,
                phone=user.phone,
            ),
        )
    except CognitoError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )


@router.post("/verify-otp", response_model=AuthTokenResponse)
async def verify_otp(body: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP code sent during registration. Returns JWT tokens on success."""
    if settings.DEMO_MODE:
        return STUB_TOKENS

    try:
        # Confirm signup
        await cognito_service.verify_otp(
            username=body.phone,
            otp_code=body.otp_code,
        )

        # Auto-login after verification
        # Note: user needs to login with password after OTP confirmation
        return AuthTokenResponse(
            access_token="",
            refresh_token="",
            user=UserResponse(
                id="",
                name="",
                email="",
                phone=body.phone,
            ),
        )
    except CognitoError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post("/refresh", response_model=AuthTokenResponse)
async def refresh(body: RefreshRequest):
    """Refresh expired access token using refresh token."""
    if settings.DEMO_MODE:
        return STUB_TOKENS

    try:
        result = await cognito_service.refresh_token(body.refresh_token)
        return AuthTokenResponse(
            access_token=result["access_token"],
            refresh_token=body.refresh_token,  # Cognito doesn't return new refresh token
            user=UserResponse(id="", name="", email="", phone=""),
        )
    except CognitoError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return UserResponse(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
    )
