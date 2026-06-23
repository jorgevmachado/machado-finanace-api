from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime, date

from app.models import TransactionTypeEnum, TransactionStatusEnum


class PayloadTransactionCreateSchema(BaseModel):
    
    type: TransactionTypeEnum
    status: TransactionStatusEnum
    amount: float
    paid_at: datetime | None = None
    account_id: UUID
    category_id: UUID
    description: str
    allocation_id: UUID
    transaction_date: date
    


class PayloadTransactionUpdateSchema(BaseModel):

    type: TransactionTypeEnum | None = None
    status: TransactionStatusEnum | None = None
    amount: float | None = None
    paid_at: datetime | None = None
    finance_id: UUID | None = None
    account_id: UUID | None = None
    category_id: UUID | None = None
    description: str | None = None
    allocation_id: UUID | None = None
    transaction_date: date | None = None


class TransactionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    type: TransactionTypeEnum    
    status: TransactionStatusEnum
    amount: float
    paid_at: datetime    
    finance_id: UUID
    account_id: UUID
    category_id: UUID
    description: str
    allocation_id: UUID            
    transaction_date: date        
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
