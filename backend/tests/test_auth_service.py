"""Tests for CognitoService -- all Cognito calls mocked via unittest.mock."""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.modules.auth.cognito_service import CognitoError, CognitoService


def _make_client_error(code: str, message: str, operation: str) -> ClientError:
    """Helper to build a boto3 ClientError with the given error code."""
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        operation,
    )


@pytest.fixture
def cognito_service():
    """Create a CognitoService with its boto3 client mocked out."""
    with patch("app.modules.auth.cognito_service.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        service = CognitoService()
        # Replace the real client with the mock for assertion access
        service._client = mock_client
        yield service


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_success(cognito_service: CognitoService):
    """Successful registration returns user_sub and confirmed status."""
    cognito_service._client.sign_up.return_value = {
        "UserSub": "sub-123",
        "UserConfirmed": False,
    }

    result = await cognito_service.register(
        email="user@example.com",
        phone="+919999999999",
        password="Str0ngP@ss!",
        name="Test User",
        company_name="Acme Ltd",
        gstin="27AABCU9603R1ZM",
    )

    assert result["user_sub"] == "sub-123"
    assert result["confirmed"] is False
    cognito_service._client.sign_up.assert_called_once()


@pytest.mark.asyncio
async def test_register_user_exists(cognito_service: CognitoService):
    """Registration with existing email raises CognitoError with USER_EXISTS."""
    cognito_service._client.sign_up.side_effect = _make_client_error(
        "UsernameExistsException", "User already exists", "SignUp"
    )

    with pytest.raises(CognitoError) as exc_info:
        await cognito_service.register(
            email="dup@example.com",
            phone="+919999999998",
            password="Str0ngP@ss!",
            name="Dup User",
            company_name="Dup Ltd",
            gstin="27AABCU9603R1ZM",
        )

    assert exc_info.value.code == "USER_EXISTS"


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_success(cognito_service: CognitoService):
    """Successful login returns access_token, refresh_token, id_token, and expires_in."""
    cognito_service._client.initiate_auth.return_value = {
        "AuthenticationResult": {
            "AccessToken": "access-tok-abc",
            "RefreshToken": "refresh-tok-xyz",
            "IdToken": "id-tok-123",
            "ExpiresIn": 3600,
        }
    }

    result = await cognito_service.login(
        username="user@example.com",
        password="Str0ngP@ss!",
    )

    assert result["access_token"] == "access-tok-abc"
    assert result["refresh_token"] == "refresh-tok-xyz"
    assert result["id_token"] == "id-tok-123"
    assert result["expires_in"] == 3600


@pytest.mark.asyncio
async def test_login_invalid_credentials(cognito_service: CognitoService):
    """Login with wrong password raises CognitoError with INVALID_CREDENTIALS."""
    cognito_service._client.initiate_auth.side_effect = _make_client_error(
        "NotAuthorizedException", "Incorrect username or password.", "InitiateAuth"
    )

    with pytest.raises(CognitoError) as exc_info:
        await cognito_service.login(
            username="user@example.com",
            password="WrongPass",
        )

    assert exc_info.value.code == "INVALID_CREDENTIALS"


# ---------------------------------------------------------------------------
# verify_otp
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_otp_success(cognito_service: CognitoService):
    """Successful OTP verification returns confirmed=True."""
    cognito_service._client.confirm_sign_up.return_value = {}

    result = await cognito_service.verify_otp(
        username="user@example.com",
        otp_code="123456",
    )

    assert result == {"confirmed": True}
    cognito_service._client.confirm_sign_up.assert_called_once()


@pytest.mark.asyncio
async def test_verify_otp_invalid(cognito_service: CognitoService):
    """Invalid OTP raises CognitoError with INVALID_OTP."""
    cognito_service._client.confirm_sign_up.side_effect = _make_client_error(
        "CodeMismatchException", "Invalid verification code", "ConfirmSignUp"
    )

    with pytest.raises(CognitoError) as exc_info:
        await cognito_service.verify_otp(
            username="user@example.com",
            otp_code="000000",
        )

    assert exc_info.value.code == "INVALID_OTP"


# ---------------------------------------------------------------------------
# refresh_token
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_token_success(cognito_service: CognitoService):
    """Successful token refresh returns new access_token and id_token."""
    cognito_service._client.initiate_auth.return_value = {
        "AuthenticationResult": {
            "AccessToken": "new-access-tok",
            "IdToken": "new-id-tok",
            "ExpiresIn": 3600,
        }
    }

    result = await cognito_service.refresh_token(refresh_token="old-refresh-tok")

    assert result["access_token"] == "new-access-tok"
    assert result["id_token"] == "new-id-tok"
    assert result["expires_in"] == 3600

    # Verify the correct auth flow was used
    call_kwargs = cognito_service._client.initiate_auth.call_args[1]
    assert call_kwargs["AuthFlow"] == "REFRESH_TOKEN_AUTH"
    assert call_kwargs["AuthParameters"]["REFRESH_TOKEN"] == "old-refresh-tok"
