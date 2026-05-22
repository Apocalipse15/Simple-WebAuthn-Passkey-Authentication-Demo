import uuid
from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID, BYTEA
from sqlalchemy.orm import Mapped, mapped_column, declarative_base, relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    display_name: Mapped[str] = mapped_column(String, nullable=False)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    webauthn_user_handle: Mapped[bytes] = mapped_column(
        BYTEA,
        nullable=False,
    )

    credentials = relationship(
        "Credential",
        back_populates="user",
        cascade="all, delete-orphan",
    )