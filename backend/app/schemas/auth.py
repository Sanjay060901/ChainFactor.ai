"""Auth request/response schemas."""

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    phone: str
    email: str
    password: str
    name: str
    company_name: str
    gstin: str


class RegisterResponse(BaseModel):
    user_id: str
    message: str


class LoginRequest(BaseModel):
    phone_or_email: str
    password: str


class VerifyOTPRequest(BaseModel):
    phone: str
    otp_code: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserResponse
