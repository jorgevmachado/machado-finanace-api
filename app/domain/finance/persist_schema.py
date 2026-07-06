from pydantic import BaseModel

from app.domain.finance.months.schema import PayloadMonthPersistSchema
from app.models import AccountTypeEnum


class PayloadPersistIncomeSchema(BaseModel):
    months: list[PayloadMonthPersistSchema]
    source: str
    description: str


class PayloadPersistChildrenExpenseSchema(BaseModel):
    name: str
    months: list[PayloadMonthPersistSchema] | None = []
    description: str


class PayloadPersistChildrenCategorySchema(BaseModel):
    name: str
    months: list[PayloadMonthPersistSchema] | None = []
    expenses: list[PayloadPersistChildrenExpenseSchema] | None = []
    description: str


class PayloadPersistParentExpenseSchema(BaseModel):
    name: str
    months: list[PayloadMonthPersistSchema] | None = []
    categories: list[PayloadPersistChildrenCategorySchema] | None = []
    description: str


class PayloadPersistCategorySchema(BaseModel):
    name: str
    description: str
    expenses: list[PayloadPersistParentExpenseSchema] = []


class PayloadPersistAllocationSchema(BaseModel):
    name: str
    description: str
    categories: list[PayloadPersistCategorySchema] = []


class PayloadPersistSchema(BaseModel):
    name: str
    type: AccountTypeEnum
    incomes: list[PayloadPersistIncomeSchema] = []
    allocations: list[PayloadPersistAllocationSchema] = []
    initial_balance: float
    reference_day: int | None = None
    reference_year: int
