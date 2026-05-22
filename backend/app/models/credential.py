import uuid
from sqlalchemy import ForeignKey, LargeBinary, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.models.base import Base


class Credential(Base):
    __tablename__ = "credentials"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    credential_id: Mapped[str]
    public_key: Mapped[str]
    sign_count: Mapped[int]
    aaguid: Mapped[str]

    backup_eligible: Mapped[bool]
    backup_state: Mapped[bool]

    attestation_type: Mapped[str]
    device_name: Mapped[str]

    last_used_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
)

    user = relationship(
        "User",
        back_populates="credentials",
    )