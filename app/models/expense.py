from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.base import default_lazy, table_registry
from app.models import utcnow

if TYPE_CHECKING:
    from app.models.finance import Finance
    from app.models.account import Account
    from app.models.allocation import Allocation
    from app.models.category import Category
    from app.models.expense_month import ExpenseMonth


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

    months: Mapped[list["ExpenseMonth"]] = relationship(
        lazy=default_lazy,
        default_factory=list,
        init=False,
        repr=False,
        back_populates="expense",
    )

    description: Mapped[str] = mapped_column(Text, nullable=False)

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
