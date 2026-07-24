from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.base import default_lazy, table_registry
from app.models import utcnow

if TYPE_CHECKING:
    from app.models.allocation_contribution import AllocationContribution


@table_registry.mapped_as_dataclass
class AllocationContributionMonth:
    __tablename__ = "allocation_contribution_months"

    allocation_contribution_id: Mapped[UUID] = mapped_column(
        ForeignKey("allocation_contributions.id"), nullable=False
    )

    allocation_contribution: Mapped["AllocationContribution"] = relationship(
        init=False,
        lazy=default_lazy,
        back_populates="months",
    )

    reference_year: Mapped[int] = mapped_column(Integer, nullable=False)

    reference_month: Mapped[int] = mapped_column(Integer, nullable=False)

    received_at: Mapped[date] = mapped_column(Date, nullable=False)

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
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
