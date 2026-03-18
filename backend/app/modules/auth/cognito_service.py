"""AWS Cognito service -- handles user registration, authentication, and token management."""

import logging

import boto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class CognitoError(Exception):
    """Raised when a Cognito operation fails."""

    def __init__(self, message: str, code: str = "COGNITO_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class CognitoService:
    """Wrapper around AWS Cognito User Pool operations."""

    def __init__(self):
        self._client = boto3.client(
            "cognito-idp",
            region_name=settings.AWS_REGION,
        )
        self._user_pool_id = settings.COGNITO_USER_POOL_ID
        self._client_id = settings.COGNITO_APP_CLIENT_ID

    async def register(
        self,
        email: str,
        phone: str,
        password: str,
        name: str,
        company_name: str,
        gstin: str,
    ) -> dict:
        """Register a new user in Cognito. Returns user_sub."""
        try:
            response = self._client.sign_up(
                ClientId=self._client_id,
                Username=email,
                Password=password,
                UserAttributes=[
                    {"Name": "email", "Value": email},
                    {"Name": "phone_number", "Value": phone},
                    {"Name": "name", "Value": name},
                    {"Name": "custom:company_name", "Value": company_name},
                    {"Name": "custom:gstin", "Value": gstin},
                ],
            )
            return {
                "user_sub": response["UserSub"],
                "confirmed": response["UserConfirmed"],
            }
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]
            logger.error("Cognito register failed: %s - %s", error_code, error_msg)

            if error_code == "UsernameExistsException":
                raise CognitoError("User already exists", code="USER_EXISTS")
            if error_code == "InvalidPasswordException":
                raise CognitoError(
                    "Password does not meet requirements", code="INVALID_PASSWORD"
                )
            if error_code == "InvalidParameterException":
                raise CognitoError(
                    f"Invalid parameter: {error_msg}", code="INVALID_PARAM"
                )
            raise CognitoError(f"Registration failed: {error_msg}", code=error_code)

    async def login(self, username: str, password: str) -> dict:
        """Authenticate user with email/phone + password. Returns tokens."""
        try:
            response = self._client.initiate_auth(
                ClientId=self._client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": username,
                    "PASSWORD": password,
                },
            )

            # Check if MFA/OTP challenge is required
            if response.get("ChallengeName"):
                return {
                    "challenge": response["ChallengeName"],
                    "session": response["Session"],
                }

            auth_result = response["AuthenticationResult"]
            return {
                "access_token": auth_result["AccessToken"],
                "refresh_token": auth_result.get("RefreshToken", ""),
                "id_token": auth_result["IdToken"],
                "expires_in": auth_result["ExpiresIn"],
            }
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]
            logger.error("Cognito login failed: %s - %s", error_code, error_msg)

            if error_code == "NotAuthorizedException":
                raise CognitoError("Invalid credentials", code="INVALID_CREDENTIALS")
            if error_code == "UserNotFoundException":
                raise CognitoError("User not found", code="USER_NOT_FOUND")
            if error_code == "UserNotConfirmedException":
                raise CognitoError(
                    "User not confirmed. Please verify OTP.", code="NOT_CONFIRMED"
                )
            raise CognitoError(f"Login failed: {error_msg}", code=error_code)

    async def verify_otp(self, username: str, otp_code: str) -> dict:
        """Confirm user signup with OTP code."""
        try:
            self._client.confirm_sign_up(
                ClientId=self._client_id,
                Username=username,
                ConfirmationCode=otp_code,
            )
            return {"confirmed": True}
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]
            logger.error("Cognito verify OTP failed: %s - %s", error_code, error_msg)

            if error_code == "CodeMismatchException":
                raise CognitoError("Invalid OTP code", code="INVALID_OTP")
            if error_code == "ExpiredCodeException":
                raise CognitoError("OTP code expired", code="OTP_EXPIRED")
            raise CognitoError(f"OTP verification failed: {error_msg}", code=error_code)

    async def refresh_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token."""
        try:
            response = self._client.initiate_auth(
                ClientId=self._client_id,
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters={
                    "REFRESH_TOKEN": refresh_token,
                },
            )
            auth_result = response["AuthenticationResult"]
            return {
                "access_token": auth_result["AccessToken"],
                "id_token": auth_result["IdToken"],
                "expires_in": auth_result["ExpiresIn"],
            }
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]
            logger.error("Cognito refresh failed: %s - %s", error_code, error_msg)
            raise CognitoError(f"Token refresh failed: {error_msg}", code=error_code)

    async def get_user(self, access_token: str) -> dict:
        """Get user attributes from Cognito using access token."""
        try:
            response = self._client.get_user(AccessToken=access_token)
            attrs = {a["Name"]: a["Value"] for a in response["UserAttributes"]}
            return {
                "sub": attrs.get("sub", ""),
                "email": attrs.get("email", ""),
                "phone": attrs.get("phone_number", ""),
                "name": attrs.get("name", ""),
                "company_name": attrs.get("custom:company_name", ""),
                "gstin": attrs.get("custom:gstin", ""),
            }
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]
            logger.error("Cognito get_user failed: %s - %s", error_code, error_msg)
            raise CognitoError(f"Failed to get user: {error_msg}", code=error_code)

    async def resend_otp(self, username: str) -> dict:
        """Resend confirmation code."""
        try:
            self._client.resend_confirmation_code(
                ClientId=self._client_id,
                Username=username,
            )
            return {"sent": True}
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]
            logger.error("Cognito resend OTP failed: %s - %s", error_code, error_msg)
            raise CognitoError(f"Failed to resend OTP: {error_msg}", code=error_code)


# Singleton instance
cognito_service = CognitoService()
