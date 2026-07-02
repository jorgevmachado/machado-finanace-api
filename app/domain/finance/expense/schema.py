from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

from app.domain.finance.allocation.schema import (
    AllocationRelationSchema,
    AllocationSchema,
)
from app.domain.finance.category.schema import CategorySchema
from app.domain.finance.expense_month.schema import (
    ExpenseMonthSchema,
    PayloadExpenseMonthPersistSchema,
)


class PayloadExpenseCreateSchema(BaseModel):
    months: list[PayloadExpenseMonthPersistSchema]
    account_id: UUID
    category_id: UUID
    description: str
    allocation_id: UUID
    reference_year: int
    reference_day: int | None = None
    reference_month: int | None = None


class PayloadExpenseUpdateSchema(BaseModel):
    months: list[ExpenseMonthSchema] = []
    account_id: UUID | None = None
    category_id: UUID | None = None
    description: str | None = None
    allocation_id: UUID | None = None


class ExpenseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    months: list[ExpenseMonthSchema] = []
    category: CategorySchema
    finance_id: UUID
    account_id: UUID
    allocation: AllocationRelationSchema
    description: str
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


AllocationSchema.model_rebuild(_types_namespace={"ExpenseSchema": ExpenseSchema})
