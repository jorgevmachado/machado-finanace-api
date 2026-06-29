from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime, date

class PayloadTransferCreateSchema(BaseModel):
    
    amount: float
    description: str
    transfer_date: date
    to_account_id: UUID
    from_account_id: UUID

class PayloadTransferUpdateSchema(BaseModel):

    amount: float | None = None
    description: str | None = None
    transfer_date: date | None = None
    to_account_id: UUID | None = None
    from_account_id: UUID | None = None


class TransferSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    amount: float
    finance_id: UUID
    description: str
    transfer_date: date
    to_account_id: UUID
    from_account_id: UUID    
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
