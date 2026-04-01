"""Auth API endpoints -- self-signed JWT with DB users, Cognito optional."""

import logging
import uuid

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.modules.auth.dependencies import (
    create_access_token,
    create_refresh_token,
    get_current_user,
)
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


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


@router.post("/register", response_model=RegisterResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user. Creates user in DB with hashed password."""
    # Check if user already exists
    existing = await db.execute(
        select(User).where(
            or_(User.email == body.email, User.phone == body.phone)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email or phone already exists",
        )

    user = User(
        cognito_sub=f"local-{uuid.uuid4().hex[:16]}",
        name=body.name,
        email=body.email,
        phone=body.phone,
        company_name=body.company_name,
        gstin=body.gstin,
        password_hash=_hash_password(body.password),
    )
    db.add(user)
    await db.flush()
    logger.info("Registered new user: %s", body.email)

    return RegisterResponse(
        user_id=str(user.id),
        message="Registration successful. You can now login.",
    )


@router.post("/login", response_model=AuthTokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email/phone + password. Returns JWT tokens."""
    # Find user by email or phone
    result = await db.execute(
        select(User).where(
            or_(
                User.email == body.phone_or_email,
                User.phone == body.phone_or_email,
            )
        )
    )
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/phone or password",
        )

    if not _verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/phone or password",
        )

    access_token = create_access_token(str(user.id), user.email)
    refresh_token = create_refresh_token(str(user.id))

    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            phone=user.phone,
        ),
    )


@router.post("/verify-otp", response_model=AuthTokenResponse)
async def verify_otp(body: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP code. For DB auth, this is a no-op (login directly)."""
    # Find user by phone
    result = await db.execute(select(User).where(User.phone == body.phone))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    access_token = create_access_token(str(user.id), user.email)
    refresh_token = create_refresh_token(str(user.id))

    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            phone=user.phone,
        ),
    )


@router.post("/refresh", response_model=AuthTokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh expired access token using refresh token."""
    import jwt as pyjwt

    try:
        payload = pyjwt.decode(
            body.refresh_token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except pyjwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    access_token = create_access_token(str(user.id), user.email)

    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=body.refresh_token,
        user=UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            phone=user.phone,
        ),
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
