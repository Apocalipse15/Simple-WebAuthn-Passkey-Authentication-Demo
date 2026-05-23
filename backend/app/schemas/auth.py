from typing import Any

from pydantic import BaseModel, Field

from app.config import settings

class RegistrationBeginRequest(BaseModel):
    username: str
    display_name: str

class RegistrationCompleteRequest(BaseModel):
    username: str = Field(min_length = settings.USERNAME_MIN_LENGTH, max_length = settings.USERNAME_MAX_LENGTH)
    credential: dict[str, Any]
    device_name: str | None = Field(
        default = None,
        max_length = settings.DEVICE_NAME_MAX_LENGTH,
    )

class RegistrationOptionsResponse(BaseModel):
    options: dict[str, Any]
    challenge: bytes

class VerifiedRegistration(BaseModel):
    credential_id: bytes
    credential_public_key: bytes
    sign_count: int
    aaguid: bytes
    attestation_object: bytes
    credential_type: str
    user_verified: bool
    attestation_format: str
    credential_device_type: str
    credential_backed_up: bool
    backup_eligible: bool
    backup_state: bool


class AuthenticationBeginRequest(BaseModel):
    username: str | None = Field(
        default = None,
        min_length = settings.USERNAME_MIN_LENGTH,
        max_length = settings.USERNAME_MAX_LENGTH,
    )

class AuthenticationCompleteRequest(BaseModel):
    username: str | None = Field(
        default = None,
        min_length = settings.USERNAME_MIN_LENGTH,
        max_length = settings.USERNAME_MAX_LENGTH,
    )
    credential: dict[str, Any]