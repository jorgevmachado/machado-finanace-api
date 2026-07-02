from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime, date

class PayloadIncomeMonthPersistSchema(BaseModel):
    id: UUID | None = None
    amount: float
    received_at: date | None = None
    reference_day: int | None = None
    reference_year: int | None = None
    reference_month: int


class IncomeMonthSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    amount: float
    income_id: UUID
    received_at: date
    reference_year: int
    reference_month: int
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
