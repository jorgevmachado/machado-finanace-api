from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Enum as SAEnum, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.base import default_lazy, table_registry
from app.models import utcnow, ExpenseStatusEnum

if TYPE_CHECKING:
    from app.models.finance import Finance
    from app.models.account import Account
    from app.models.allocation import Allocation
    from app.models.category import Category


@table_registry.mapped_as_dataclass
class Expense:
    __tablename__ = "expenses"

    finance_id: Mapped[UUID] = mapped_column(ForeignKey("finances.id"), nullable=False)

    finance: Mapped["Finance"] = relationship(
        init=False,
        lazy=default_lazy,
        back_populates="expenses",
    )

    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"), nullable=False)

    account: Mapped["Account"] = relationship(
        init=False,
        lazy=default_lazy,
        back_populates="expenses",
    )

    allocation_id: Mapped[UUID] = mapped_column(
        ForeignKey("allocations.id"), nullable=False
    )

    allocation: Mapped["Allocation"] = relationship(
        init=False,
        lazy=default_lazy,
        back_populates="expenses",
    )

    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("categories.id"), nullable=False
    )

    category: Mapped["Category"] = relationship(
        init=False,
        lazy=default_lazy,
        back_populates="expenses",
    )

    description: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[ExpenseStatusEnum] = mapped_column(  # noqa: F821
        SAEnum(ExpenseStatusEnum, name="expensestatusenum"),
        nullable=False,
        default=ExpenseStatusEnum.PAID,
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
