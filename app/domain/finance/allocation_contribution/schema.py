from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

from app.domain.finance.allocation.schema import AllocationRelationSchema, AllocationSchema
from app.domain.finance.allocation_contribution_month.schema import (
    AllocationContributionMonthSchema,
)
from app.domain.finance.expense.schema import ExpenseSchema
from app.domain.finance.months.schema import PayloadMonthPersistSchema


class PayloadAllocationContributionCreateSchema(BaseModel):
    months: list[PayloadMonthPersistSchema]
    description: str
    allocation_id: UUID
    reference_day: int | None = None
    reference_year: int
    contributor_name: str


class PayloadAllocationContributionUpdateSchema(BaseModel):
    months: list[PayloadMonthPersistSchema] | None = None
    description: str | None = None
    allocation_id: UUID | None = None
    reference_day: int | None = None
    reference_year: int | None = None
    contributor_name: str | None = None


class AllocationContributionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    months: list[AllocationContributionMonthSchema] = []
    allocation: AllocationRelationSchema
    description: str | None = None
    contributor_name: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

AllocationContributionSchema.model_rebuild()
AllocationSchema.model_rebuild(
    _types_namespace={
        "AllocationContributionSchema": AllocationContributionSchema,
        "ExpenseSchema": ExpenseSchema,
    }
)