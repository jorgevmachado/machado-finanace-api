from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime, date


class PayloadIncomeCreateSchema(BaseModel):
    source: str
    amount: float
    account_id: UUID
    received_at: date
    description: str
    reference_year: int
    reference_month: int


class PayloadIncomeUpdateSchema(BaseModel):
    source: str | None = None
    amount: float | None = None
    account_id: UUID | None = None
    received_at: date | None = None
    description: str | None = None
    reference_year: int | None = None
    reference_month: int | None = None


class IncomeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source: str
    amount: float
    source_code: str
    finance_id: UUID
    account_id: UUID
    received_at: date
    description: str
    reference_year: int
    reference_month: int
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
