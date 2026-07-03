from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.models import MonthStatusEnum


class PayloadMonthPersistSchema(BaseModel):
    id: UUID | None = None
    amount: float
    status: MonthStatusEnum | None = None
    reference_day: int | None = None
    reference_month: int
    transaction_date: date | None = None
