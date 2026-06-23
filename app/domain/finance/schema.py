from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

from app.domain.finance.account.schema import AccountSchema
from app.domain.finance.allocation.schema import AllocationSchema
from app.domain.finance.allocation_contribution.schema import AllocationContributionSchema
from app.domain.finance.category.schema import CategorySchema
from app.domain.finance.income.schema import IncomeSchema
from app.domain.finance.transaction.schema import TransactionSchema


class FinanceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    incomes: list[IncomeSchema]    
    accounts: list[AccountSchema]
    categories: list[CategorySchema]       
    allocations: list[AllocationSchema]
    transactions: list[TransactionSchema]
    allocation_contributions: list[AllocationContributionSchema]
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
