from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum as SAEnum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.base import table_registry, default_lazy
from app.models import utcnow
from app.models.enums import StatusEnum, RoleEnum

if TYPE_CHECKING:
    from app.models.finance import Finance


@table_registry.mapped_as_dataclass
class User:
    __tablename__ = "users"

    # Required fields (no defaults) — must come first in __init__
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

    # Optional fields with defaults
    status: Mapped[StatusEnum] = mapped_column(
        SAEnum(StatusEnum, name="statusenum"),
        nullable=False,
        default=StatusEnum.INACTIVE,
    )
    role: Mapped[RoleEnum] = mapped_column(
        SAEnum(RoleEnum, name="roleenum"),
        nullable=False,
        default=RoleEnum.USER,
    )

    # Auto-generated / server-managed — excluded from __init__
    id: Mapped[UUID] = mapped_column(
        primary_key=True, default_factory=uuid4, init=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default_factory=utcnow, init=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, init=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, init=False
    )

    finance: Mapped["Finance | None"] = relationship(
        init=False,
        lazy=default_lazy,
        default=None,
        back_populates="user",
    )
