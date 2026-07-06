from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

from app.domain.finance.allocation.schema import (
    AllocationRelationSchema,
    AllocationSchema,
)
from app.domain.finance.category.schema import CategorySchema
from app.domain.finance.expense_month.schema import ExpenseMonthSchema
from app.domain.finance.months.schema import PayloadMonthPersistSchema


class PayloadExpenseCreateSchema(BaseModel):
    payee: str
    months: list[PayloadMonthPersistSchema]
    category_id: UUID
    description: str
    allocation_id: UUID
    reference_year: int
    reference_day: int | None = None
    reference_month: int | None = None
    parent_id: UUID | None = None


class PayloadExpenseUpdateSchema(BaseModel):
    months: list[ExpenseMonthSchema] = []
    category_id: UUID | None = None
    description: str | None = None
    allocation_id: UUID | None = None


class ExpenseParentSchema(BaseModel):
    """Simplified expense schema for parent references, preventing infinite recursion."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    description: str
    created_at: datetime


class ExpenseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    payee: str
    months: list[ExpenseMonthSchema] = []
    category: CategorySchema
    payee_code: str
    allocation: AllocationRelationSchema
    description: str
    parent_id: UUID | None = None
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class ExpenseDetailSchema(BaseModel):
    """Expense schema with parent and children relationships."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    payee: str
    months: list[ExpenseMonthSchema] = []
    category: CategorySchema
    payee_code: str
    allocation: AllocationRelationSchema
    description: str
    parent_id: UUID | None = None
    parent: ExpenseParentSchema | None = None
    children: list[ExpenseSchema] | None = None
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


ExpenseSchema.model_rebuild()
ExpenseDetailSchema.model_rebuild()

AllocationSchema.model_rebuild(_types_namespace={"ExpenseSchema": ExpenseSchema})
