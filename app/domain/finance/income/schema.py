from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

from app.domain.finance.income_month.schema import (
    IncomeMonthSchema,
    PayloadIncomeMonthPersistSchema,
)


class PayloadIncomeCreateSchema(BaseModel):
    months: list[PayloadIncomeMonthPersistSchema]
    source: str
    account_id: UUID
    description: str
    reference_year: int
    reference_day: int | None = None
    reference_month: int | None = None


class PayloadIncomeUpdateSchema(BaseModel):
    months: list[PayloadIncomeMonthPersistSchema]
    source: str | None = None
    account_id: UUID | None = None
    description: str | None = None


class IncomeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    months: list[IncomeMonthSchema] = []
    source: str
    source_code: str
    finance_id: UUID
    account_id: UUID
    description: str
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
