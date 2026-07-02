from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

from app.models import MonthStatusEnum


class PayloadExpenseMonthPersistSchema(BaseModel):
    id: UUID | None = None
    status: MonthStatusEnum | None = None
    amount: float
    paid_at: datetime | None = None
    reference_day: int | None = None
    reference_year: int | None = None
    reference_month: int


class ExpenseMonthSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: MonthStatusEnum
    amount: float
    paid_at: datetime | None = None
    expense_id: UUID
    reference_year: int
    reference_month: int
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
