from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import TYPE_CHECKING

# from app.domain.finance.allocation_contribution.schema import AllocationContributionSchema

if TYPE_CHECKING:
    from app.domain.finance.expense.schema import ExpenseSchema


class PayloadAllocationCreateSchema(BaseModel):
    name: str
    account_id: UUID
    description: str


class PayloadAllocationUpdateSchema(BaseModel):
    name: str | None = None
    is_active: bool | None = None
    account_id: UUID | None = None
    description: str | None = None


class AllocationRelationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    name_code: str
    is_active: bool
    account_id: UUID
    description: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class AllocationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    expenses: list[ExpenseSchema]
    name_code: str
    is_active: bool
    account_id: UUID
    description: str | None = None
    # allocation_contributions: list[AllocationContributionSchema]
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
