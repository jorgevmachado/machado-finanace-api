from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

from app.domain.finance.account.schema import AccountSchema
from app.domain.finance.allocation.schema import AllocationSchema


class FinanceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    accounts: list[AccountSchema]
    allocations: list[AllocationSchema]
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
