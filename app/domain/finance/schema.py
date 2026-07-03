from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

from app.domain.finance.account.schema import AccountSchema, PayloadAccountCreateSchema
from app.domain.finance.allocation.schema import (
    AllocationSchema,
    PayloadAllocationCreateSchema,
)
from app.domain.finance.category.schema import (
    PayloadCategoryCreateSchema,
)

from app.domain.finance.months.schema import PayloadMonthPersistSchema


class FinanceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    accounts: list[AccountSchema]
    allocations: list[AllocationSchema]
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


# PERSIST ALL
class PayloadFinanceChildrenExpensePersistSchema(PayloadCategoryCreateSchema):
    amount: float
    reference_day: int | None = None
    reference_month: int | None = None


class PayloadFinanceExpensePersistSchema(PayloadMonthPersistSchema):
    children: list[PayloadFinanceChildrenExpensePersistSchema] | None = []
    reference_month: int | None = None


class PayloadFinanceCategoryPersistSchema(PayloadCategoryCreateSchema):
    expenses: list[PayloadFinanceExpensePersistSchema]


class PayloadFinanceAllocationPersistSchema(PayloadAllocationCreateSchema):
    categories: list[PayloadFinanceCategoryPersistSchema]


class PayloadFinanceIncomePersistSchema(BaseModel):
    months: list[PayloadMonthPersistSchema]
    source: str
    description: str


class PayloadFinancePersistSchema(PayloadAccountCreateSchema):
    incomes: list[PayloadFinanceIncomePersistSchema] = []
    allocations: list[PayloadFinanceAllocationPersistSchema] = []
    reference_day: int | None = None
    reference_year: int


class FinancePersistResultSchema(BaseModel):
    incomes: int
    accounts: int
    expenses: int
    categories: int
    allocations: int
