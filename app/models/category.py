from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.base import default_lazy, table_registry
from app.models import utcnow, CategoryTypeEnum

if TYPE_CHECKING:
    from app.models.finance import Finance
    from app.models.transaction import Transaction


@table_registry.mapped_as_dataclass
class Category:
    __tablename__ = "categories"

    finance_id: Mapped[UUID] = mapped_column(ForeignKey("finances.id"), nullable=False)

    finance: Mapped["Finance"] = relationship(
        init=False,
        lazy=default_lazy,
        back_populates="categories",
    )

    name: Mapped[str] = mapped_column(String, nullable=False)

    name_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=False)

    type: Mapped[CategoryTypeEnum] = mapped_column(
        SAEnum(CategoryTypeEnum, name="categorytypeenum"),
        nullable=False,
        default=CategoryTypeEnum.OTHER,
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        lazy=default_lazy,
        default_factory=list,
        init=False,
        repr=False,
        back_populates="category",
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
