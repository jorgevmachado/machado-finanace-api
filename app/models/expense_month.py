from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Enum as SAEnum, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.base import default_lazy, table_registry
from app.models import utcnow, MonthStatusEnum

if TYPE_CHECKING:
    from app.models.expense import Expense


@table_registry.mapped_as_dataclass
class ExpenseMonth:
    __tablename__ = "expense_months"

    expense_id: Mapped[UUID] = mapped_column(ForeignKey("expenses.id"), nullable=False)

    expense: Mapped["Expense"] = relationship(
        init=False,
        lazy=default_lazy,
        back_populates="months",
    )

    reference_year: Mapped[int] = mapped_column(Integer, nullable=False)

    reference_month: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[MonthStatusEnum] = mapped_column(  # noqa: F821
        SAEnum(MonthStatusEnum, name="monthstatusenum"),
        nullable=False,
        default=MonthStatusEnum.PENDING,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
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
