from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Date, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.base import default_lazy, table_registry
from app.models import utcnow

if TYPE_CHECKING:
    from app.models.finance import Finance
    from app.models.account import Account


@table_registry.mapped_as_dataclass
class Transfer:
    __tablename__ = "transfers"

    finance_id: Mapped[UUID] = mapped_column(ForeignKey("finances.id"), nullable=False)

    finance: Mapped["Finance"] = relationship(
        init=False,
        lazy=default_lazy,
        back_populates="transfers",
    )

    to_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.id"), nullable=False
    )

    to_account: Mapped["Account"] = relationship(
        init=False,
        lazy=default_lazy,
        back_populates="incoming_transfers",
        foreign_keys=[to_account_id],
    )

    from_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.id"), nullable=False
    )

    from_account: Mapped["Account"] = relationship(
        init=False,
        lazy=default_lazy,
        back_populates="outgoing_transfers",
        foreign_keys=[from_account_id],
    )

    description: Mapped[str] = mapped_column(Text, nullable=False)

    transfer_date: Mapped[date] = mapped_column(Date, nullable=False)

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
