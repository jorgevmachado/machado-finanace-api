from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime, date

from app.domain.finance.allocation.schema import AllocationSchema
from app.domain.finance.category.schema import CategorySchema
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

class PayloadTransactionCreateListItemSchema(BaseModel):
    status: TransactionStatusEnum
    amount: float
    reference_month: int
    paid_at: datetime | None = None
    transaction_date: date | None = None

class PayloadTransactionCreateListCategoryItemSchema(BaseModel):
    type: TransactionTypeEnum
    category_id: UUID
    description: str
    reference_day: int | None = None
    transactions: list[PayloadTransactionCreateListItemSchema]

class PayloadTransactionCreateListSchema(BaseModel):
    account_id: UUID
    reference_day: int | None = None
    allocation_id: UUID
    reference_year: int | None = None
    categories: list[PayloadTransactionCreateListCategoryItemSchema]

class PayloadTransactionUpdateSchema(BaseModel):
    type: TransactionTypeEnum | None = None
    status: TransactionStatusEnum | None = None
    amount: float | None = None
    paid_at: datetime | None = None
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
    category: CategorySchema
    paid_at: datetime
    finance_id: UUID
    account_id: UUID
    description: str
    allocation: AllocationSchema
    transaction_date: date
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
