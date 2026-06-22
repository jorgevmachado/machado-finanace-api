from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

from app.models import AccountTypeEnum


class PayloadAccountCreateSchema(BaseModel):
    name: str
    type: AccountTypeEnum
    initial_balance: float

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
    is_active: bool
    finance_id: UUID
    initial_balance: float
    current_balance: float
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

