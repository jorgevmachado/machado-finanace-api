from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime, date

from app.domain.finance.allocation.schema import (
    AllocationRelationSchema,
    AllocationSchema,
)
from app.domain.finance.category.schema import CategorySchema
from app.domain.finance.expense_month.schema import ExpenseMonthSchema
from app.domain.finance.months.schema import PayloadMonthPersistSchema
from app.models import BankEnum


class PayloadExpenseCreateSchema(BaseModel):
    payee: str
    months: list[PayloadMonthPersistSchema]
    parent_id: UUID | None = None
    category_id: UUID
    description: str
    allocation_id: UUID
    reference_year: int
    reference_day: int | None = None


class PayloadExpenseUpdateSchema(BaseModel):
    payee: str | None = None
    months: list[PayloadMonthPersistSchema] | None = None
    parent_id: UUID | None = None
    category_id: UUID | None = None
    description: str | None = None
    allocation_id: UUID | None = None
    reference_day: int | None = None
    reference_year: int | None = None

class UploadedExpenseResultSchema(BaseModel):
    date: date
    payee: str
    amount: float
    category: CategorySchema
    reference_month: int
    current_installment: int
    total_of_installments: int

class UploadedResultSchema(BaseModel):
    bank: BankEnum
    error: bool
    message: str
    category: CategorySchema
    expenses: list[UploadedExpenseResultSchema]
    allocation: AllocationSchema
    bill_total: float
    bill_due_date: date | None = None
    date_of_issue: date | None = None
    reference_year: int
    reference_month: int
    previous_bill_total: float
    previous_bill_due_date: date | None = None

class PayloadExpenseListPersist(BaseModel):
    parent: PayloadExpenseCreateSchema | None = None
    expenses: list[PayloadExpenseCreateSchema]

class ExpenseParentSchema(BaseModel):
    """Simplified expense schema for parent references, preventing infinite recursion."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    description: str
    created_at: datetime

class ExpenseBaseSchema(BaseModel):
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
    children: list[ExpenseBaseSchema] | None = []


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
