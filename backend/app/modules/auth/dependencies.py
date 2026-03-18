"""Auth dependencies for FastAPI route protection."""

import logging
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.modules.auth.jwt_service import JWTError_, verify_cognito_token

logger = logging.getLogger(__name__)

# Bearer token extractor
bearer_scheme = HTTPBearer(auto_error=False)

# Stub user for DEMO_MODE
DEMO_USER_SUB = "demo-user-sub-00000000"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and verify JWT from Authorization header, return User from DB.

    In DEMO_MODE, returns a stub user without JWT verification.
    """
    # --- DEMO MODE: skip JWT, return/create stub user ---
    if settings.DEMO_MODE:
        return await _get_or_create_demo_user(db)

    # --- PRODUCTION: verify Cognito JWT ---
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims = await verify_cognito_token(credentials.credentials)
    except JWTError_ as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    cognito_sub = claims.get("sub")
    if not cognito_sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' claim",
        )

    # Look up user in DB by cognito_sub
    result = await db.execute(select(User).where(User.cognito_sub == cognito_sub))
    user = result.scalar_one_or_none()

    if not user:
        # First login after Cognito registration -- create DB record
        user = User(
            cognito_sub=cognito_sub,
            name=claims.get("name", ""),
            email=claims.get("email", ""),
            phone=claims.get("phone_number", ""),
            company_name=claims.get("custom:company_name", ""),
            gstin=claims.get("custom:gstin", ""),
        )
        db.add(user)
        await db.flush()
        logger.info("Created new user from Cognito: %s", cognito_sub)

    return user


async def _get_or_create_demo_user(db: AsyncSession) -> User:
    """Get or create the demo user for DEMO_MODE."""
    result = await db.execute(select(User).where(User.cognito_sub == DEMO_USER_SUB))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            cognito_sub=DEMO_USER_SUB,
            name="Demo User",
            email="demo@chainfactor.ai",
            phone="+919876543210",
            company_name="Acme Technologies Pvt Ltd",
            gstin="27AABCU9603R1ZM",
            wallet_address="ALGO7DEMO2ADDRESS3FOR4TESTING5WALLET6X4F2ABC",
        )
        db.add(user)
        await db.flush()
        logger.info("Created demo user")

    return user


def require_owner(invoice_user_id: uuid.UUID, current_user: User) -> None:
    """IDOR prevention: verify the resource belongs to the current user.

    Usage in endpoints:
        require_owner(invoice.user_id, current_user)
    """
    if invoice_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this resource",
        )
