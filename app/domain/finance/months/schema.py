from datetime import date

from pydantic import BaseModel

from app.models import MonthStatusEnum


class PayloadMonthPersistSchema(BaseModel):
    amount: float
    status: MonthStatusEnum | None = None
    reference_day: int | None = None
    reference_month: int
    transaction_date: date | None = None
