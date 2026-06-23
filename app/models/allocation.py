from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Boolean, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.base import default_lazy, table_registry
from app.models import utcnow, AllocationTypeEnum

if TYPE_CHECKING:
    from app.models.finance import Finance
    from app.models.allocation_contribution import AllocationContribution
    from app.models.transaction import Transaction


@table_registry.mapped_as_dataclass
class Allocation:
    __tablename__ = "allocations"

    finance_id: Mapped[UUID] = mapped_column(ForeignKey("finances.id"), nullable=False)

    finance: Mapped["Finance"] = relationship(
        init=False,
        lazy=default_lazy,
        back_populates="allocations",
    )

    name: Mapped[str] = mapped_column(String, nullable=False)

    name_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=False)

    type: Mapped[AllocationTypeEnum] = mapped_column(
        SAEnum(AllocationTypeEnum, name="allocationtypeenum"),
        nullable=False,
        default=AllocationTypeEnum.OTHER,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    allocation_contributions: Mapped[list["AllocationContribution"]] = relationship(
        lazy=default_lazy,
        default_factory=list,
        init=False,
        repr=False,
        back_populates="allocation",
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        lazy=default_lazy,
        default_factory=list,
        init=False,
        repr=False,
        back_populates="allocation",
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
