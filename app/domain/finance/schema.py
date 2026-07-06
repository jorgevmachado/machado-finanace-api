from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

from app.domain.finance.account.schema import AccountSchema
from app.domain.finance.category.schema import CategorySchema


class FinanceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    accounts: list[AccountSchema]
    categories: list[CategorySchema]
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

class FinancePersistResultSchema(BaseModel):
    incomes: int
    accounts: int
    expenses: int
    categories: int
    allocations: int
