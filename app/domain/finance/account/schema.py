from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

from app.domain.finance.allocation_contribution.schema import AllocationContributionSchema
from app.domain.finance.expense.schema import ExpenseSchema
from app.domain.finance.income.schema import IncomeSchema
from app.domain.finance.transfer.schema import TransferSchema
from app.models import AccountTypeEnum


class PayloadAccountCreateSchema(BaseModel):
    name: str
    type: AccountTypeEnum
    initial_balance: float


class PayloadAccountCreateListSchema(BaseModel):
    accounts: list[PayloadAccountCreateSchema]


class PayloadAccountUpdateSchema(BaseModel):
    name: str | None = None
    type: AccountTypeEnum | None = None
    is_active: bool | None = None
    initial_balance: float | None = None
    current_balance: float | None = None


class AccountSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    type: AccountTypeEnum
    incomes: list[IncomeSchema]    
    is_active: bool
    finance_id: UUID
    expenses: list[ExpenseSchema]
    incoming_transfers: list[TransferSchema]
    outgoing_transfers: list[TransferSchema]
    initial_balance: float
    current_balance: float
    allocation_contributions: list[AllocationContributionSchema]
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
