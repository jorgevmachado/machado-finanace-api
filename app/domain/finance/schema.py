from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

from app.domain.finance.account.schema import AccountSchema
from app.domain.finance.allocation.schema import AllocationSchema
from app.models import (
    AccountTypeEnum,
    AllocationTypeEnum,
    CategoryTypeEnum,
    ExpenseStatusEnum,
)


class FinanceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    accounts: list[AccountSchema]
    allocations: list[AllocationSchema]
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

class FinanceCreateMonthSchema(BaseModel):
    amount: float
    status: ExpenseStatusEnum | None = None
    reference_day: int | None = None
    reference_month: int

class FinanceCreateIncomeSchema(BaseModel):
    source: str
    months: list[FinanceCreateMonthSchema]
    description: str | None = None

class FinanceCreateCategorySchema(BaseModel):
    name: str
    type: CategoryTypeEnum
    months: list[FinanceCreateMonthSchema]
    description: str | None = None

class FinanceCreateContributionsSchema(BaseModel):    
    months: list[FinanceCreateMonthSchema]
    description: str | None = None
    contributor_name: str

class FinanceCreateAllocationSchema(BaseModel):
    name: str
    type: AllocationTypeEnum
    categories: list[FinanceCreateCategorySchema]
    description: str | None = None
    contributions: list[FinanceCreateContributionsSchema] = []
    

class FinanceCreateSchema(BaseModel):
    name: str
    type: AccountTypeEnum
    incomes: list[FinanceCreateIncomeSchema] = []
    allocations: list[FinanceCreateAllocationSchema] = []
    reference_day: int | None = None
    reference_year: int
    initialize_balance: int | None = None
    