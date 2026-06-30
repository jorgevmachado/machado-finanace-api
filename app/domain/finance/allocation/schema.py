from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import TYPE_CHECKING

from app.models import AllocationTypeEnum

if TYPE_CHECKING:
    from app.domain.finance.expense.schema import ExpenseSchema



class PayloadAllocationCreateSchema(BaseModel):
    name: str
    type: AllocationTypeEnum
    description: str


class PayloadAllocationUpdateSchema(BaseModel):
    name: str | None = None
    type: AllocationTypeEnum | None = None
    is_active: bool | None = None
    description: str | None = None


class AllocationRelationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    type: AllocationTypeEnum
    name_code: str
    is_active: bool
    finance_id: UUID
    description: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class AllocationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    type: AllocationTypeEnum
    expenses: list[ExpenseSchema]
    name_code: str
    is_active: bool    
    finance_id: UUID
    description: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
