from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime, date

from app.domain.finance.allocation.schema import AllocationRelationSchema, AllocationSchema
from app.domain.finance.category.schema import CategorySchema
from app.models import ExpenseStatusEnum

class PayloadExpenseCreateSchema(BaseModel):
    status: ExpenseStatusEnum
    amount: float
    paid_at: datetime | None = None
    account_id: UUID
    category_id: UUID
    description: str
    allocation_id: UUID
    reference_day: int | None = None
    reference_year: int | None = None
    reference_month: int | None = None

class PayloadExpenseUpdateSchema(BaseModel):
    status: ExpenseStatusEnum | None = None
    amount: float | None = None
    paid_at: datetime | None = None
    account_id: UUID | None = None
    category_id: UUID | None = None
    description: str | None = None
    allocation_id: UUID | None = None
    transaction_date: date | None = None


class ExpenseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: ExpenseStatusEnum
    amount: float
    paid_at: datetime | None = None
    finance_id: UUID
    account_id: UUID
    category: CategorySchema
    allocation: AllocationRelationSchema
    description: str
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

AllocationSchema.model_rebuild(_types_namespace={"ExpenseSchema": ExpenseSchema})