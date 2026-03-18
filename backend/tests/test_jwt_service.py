"""Tests for JWT verification with mocked JWKS endpoint."""

import base64
import time
from unittest.mock import AsyncMock, patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt as jose_jwt

import app.modules.auth.jwt_service as jwt_module
from app.modules.auth.jwt_service import JWTError_, verify_cognito_token

# ---------------------------------------------------------------------------
# Test RSA key pair + JWKS helpers
# ---------------------------------------------------------------------------

TEST_KID = "test-key-id-001"
TEST_REGION = "ap-south-1"
TEST_POOL_ID = "ap-south-1_TestPool"
TEST_CLIENT_ID = "test-client-id-abc"
TEST_ISSUER = f"https://cognito-idp.{TEST_REGION}.amazonaws.com/{TEST_POOL_ID}"


def _generate_rsa_keypair():
    """Generate an RSA private key and return (private_key, public_key) objects."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


def _private_key_pem(private_key) -> str:
    """Serialize RSA private key to PEM string."""
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


def _int_to_base64url(n: int) -> str:
    """Convert a Python int to base64url-encoded string (JWKS format)."""
    byte_length = (n.bit_length() + 7) // 8
    raw = n.to_bytes(byte_length, byteorder="big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _build_jwks(public_key, kid: str = TEST_KID) -> dict:
    """Build a JWKS dict containing one RSA public key."""
    pub_numbers = public_key.public_numbers()
    return {
        "keys": [
            {
                "kty": "RSA",
                "kid": kid,
                "use": "sig",
                "alg": "RS256",
                "n": _int_to_base64url(pub_numbers.n),
                "e": _int_to_base64url(pub_numbers.e),
            }
        ]
    }


def _sign_jwt(
    private_key,
    claims: dict,
    kid: str = TEST_KID,
    algorithm: str = "RS256",
) -> str:
    """Create a signed JWT string."""
    return jose_jwt.encode(
        claims,
        _private_key_pem(private_key),
        algorithm=algorithm,
        headers={"kid": kid},
    )


def _default_claims(**overrides) -> dict:
    """Build a set of valid Cognito-like JWT claims."""
    now = int(time.time())
    claims = {
        "sub": "test-sub-uuid",
        "email": "test@chainfactor.ai",
        "token_use": "access",
        "iss": TEST_ISSUER,
        "aud": TEST_CLIENT_ID,
        "iat": now,
        "exp": now + 3600,
    }
    claims.update(overrides)
    return claims


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_jwks_cache():
    """Clear the module-level JWKS cache before every test."""
    jwt_module._jwks_cache = None
    jwt_module._jwks_fetched_at = 0
    yield
    jwt_module._jwks_cache = None
    jwt_module._jwks_fetched_at = 0


@pytest.fixture
def rsa_keys():
    """Provide a fresh RSA key pair for each test."""
    private_key, public_key = _generate_rsa_keypair()
    return private_key, public_key


@pytest.fixture
def mock_settings():
    """Patch settings with test Cognito values."""
    with (
        patch.object(jwt_module.settings, "AWS_REGION", TEST_REGION),
        patch.object(jwt_module.settings, "COGNITO_USER_POOL_ID", TEST_POOL_ID),
        patch.object(jwt_module.settings, "COGNITO_APP_CLIENT_ID", TEST_CLIENT_ID),
    ):
        yield


def _patch_jwks_fetch(jwks_response: dict):
    """Return a context manager that mocks httpx.AsyncClient.get to return jwks_response."""
    from unittest.mock import MagicMock as _MagicMock

    # httpx.Response.json() and .raise_for_status() are synchronous -- use MagicMock
    mock_response = _MagicMock()
    mock_response.json.return_value = jwks_response
    mock_response.raise_for_status.return_value = None

    mock_client_instance = AsyncMock()
    mock_client_instance.get.return_value = mock_response
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = False

    return patch(
        "app.modules.auth.jwt_service.httpx.AsyncClient",
        return_value=mock_client_instance,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_valid_token(rsa_keys, mock_settings):
    """A properly signed token with valid claims returns the decoded claims."""
    private_key, public_key = rsa_keys
    jwks = _build_jwks(public_key)
    token = _sign_jwt(private_key, _default_claims())

    with _patch_jwks_fetch(jwks):
        claims = await verify_cognito_token(token)

    assert claims["sub"] == "test-sub-uuid"
    assert claims["email"] == "test@chainfactor.ai"
    assert claims["token_use"] == "access"


@pytest.mark.asyncio
async def test_verify_expired_token(rsa_keys, mock_settings):
    """An expired token raises JWTError_."""
    private_key, public_key = rsa_keys
    jwks = _build_jwks(public_key)

    expired_claims = _default_claims(
        iat=int(time.time()) - 7200,
        exp=int(time.time()) - 3600,
    )
    token = _sign_jwt(private_key, expired_claims)

    with _patch_jwks_fetch(jwks):
        with pytest.raises(JWTError_):
            await verify_cognito_token(token)


@pytest.mark.asyncio
async def test_verify_invalid_kid(rsa_keys, mock_settings):
    """A token whose kid does not match any JWKS key raises JWTError_."""
    private_key, public_key = rsa_keys
    # JWKS contains key with different kid
    jwks = _build_jwks(public_key, kid="some-other-kid")
    token = _sign_jwt(private_key, _default_claims(), kid="mismatched-kid")

    with _patch_jwks_fetch(jwks):
        with pytest.raises(JWTError_):
            await verify_cognito_token(token)


@pytest.mark.asyncio
async def test_jwks_caching(rsa_keys, mock_settings):
    """JWKS is fetched only once for multiple verify calls (cache hit)."""
    private_key, public_key = rsa_keys
    jwks = _build_jwks(public_key)

    token1 = _sign_jwt(private_key, _default_claims(sub="user-1"))
    token2 = _sign_jwt(private_key, _default_claims(sub="user-2"))

    with _patch_jwks_fetch(jwks) as mock_client_cls:
        await verify_cognito_token(token1)
        await verify_cognito_token(token2)

        # httpx.AsyncClient was instantiated only once (first call fetches, second uses cache)
        assert mock_client_cls.call_count == 1
