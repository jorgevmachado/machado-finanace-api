from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Boolean, Enum as SAEnum, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.base import default_lazy, table_registry
from app.models import utcnow, AccountTypeEnum

if TYPE_CHECKING:
    from app.models.finance import Finance


@table_registry.mapped_as_dataclass
class Account:
    __tablename__ = "accounts"

    finance_id: Mapped[UUID] = mapped_column(ForeignKey("finances.id"), nullable=False)

    finance: Mapped["Finance"] = relationship(
        init=False,
        lazy=default_lazy,
        back_populates="accounts",
    )

    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    type: Mapped[AccountTypeEnum] = mapped_column(
        SAEnum(AccountTypeEnum, name="accounttypeenum"),
        nullable=False,
        default=AccountTypeEnum.BANK,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    initial_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    current_balance: Mapped[Decimal] = mapped_column(
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
