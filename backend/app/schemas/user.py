from pydantic import BaseModel, Field
import base64

from uuid import UUID


class UserCreate(BaseModel):
    username: str
    display_name: str
    is_verified: bool = False

    # we'll accept base64 for bytes (clean API design)
    webauthn_user_handle: str = Field(
        description="Base64-encoded bytes"
    )


class UserRead(BaseModel):
    id: UUID
    username: str
    display_name: str
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True