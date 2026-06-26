from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

from app.domain.finance.account.schema import AccountSchema

class FinanceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    accounts: list[AccountSchema]
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
