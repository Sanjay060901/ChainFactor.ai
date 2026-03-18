"""JWT verification for Cognito tokens using JWKS (JSON Web Key Set)."""

import logging
import time

import httpx
from jose import JWTError, jwk, jwt

from app.config import settings

logger = logging.getLogger(__name__)

# JWKS cache: fetched once, cached in memory
_jwks_cache: dict | None = None
_jwks_fetched_at: float = 0
JWKS_CACHE_TTL_SECONDS = 3600  # Re-fetch JWKS every hour


class JWTError_(Exception):
    """Raised when JWT validation fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def _get_jwks_url() -> str:
    """Build Cognito JWKS URL from pool ID."""
    region = settings.AWS_REGION
    pool_id = settings.COGNITO_USER_POOL_ID
    return f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json"


def _get_issuer() -> str:
    """Build Cognito issuer URL from pool ID."""
    region = settings.AWS_REGION
    pool_id = settings.COGNITO_USER_POOL_ID
    return f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"


async def _fetch_jwks() -> dict:
    """Fetch JWKS from Cognito. Cached for JWKS_CACHE_TTL_SECONDS."""
    global _jwks_cache, _jwks_fetched_at

    now = time.time()
    if _jwks_cache and (now - _jwks_fetched_at) < JWKS_CACHE_TTL_SECONDS:
        return _jwks_cache

    url = _get_jwks_url()
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        _jwks_cache = response.json()
        _jwks_fetched_at = now
        logger.info(
            "Fetched JWKS from Cognito (%d keys)", len(_jwks_cache.get("keys", []))
        )
        return _jwks_cache


def _get_signing_key(jwks: dict, kid: str) -> str:
    """Find the signing key matching the token's kid header."""
    for key in jwks.get("keys", []):
        if key["kid"] == kid:
            return jwk.construct(key).to_pem().decode("utf-8")
    raise JWTError_(f"Signing key not found for kid: {kid}")


async def verify_cognito_token(token: str) -> dict:
    """Verify and decode a Cognito JWT (access or ID token).

    Returns the decoded claims dict with keys like:
    - sub: user's Cognito sub (UUID)
    - email: user's email
    - token_use: "access" or "id"
    """
    try:
        # Decode header without verification to get kid
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise JWTError_("Token header missing 'kid'")

        # Fetch JWKS and find matching key
        jwks = await _fetch_jwks()
        signing_key = _get_signing_key(jwks, kid)

        # Verify and decode
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.COGNITO_APP_CLIENT_ID,
            issuer=_get_issuer(),
            options={
                "verify_exp": True,
                "verify_aud": True,
                "verify_iss": True,
            },
        )

        # Validate token_use
        token_use = claims.get("token_use")
        if token_use not in ("access", "id"):
            raise JWTError_(f"Invalid token_use: {token_use}")

        return claims

    except JWTError as e:
        logger.warning("JWT verification failed: %s", str(e))
        raise JWTError_(f"Invalid token: {str(e)}")
    except httpx.HTTPError as e:
        logger.error("Failed to fetch JWKS: %s", str(e))
        raise JWTError_(f"Failed to verify token (JWKS fetch error): {str(e)}")
