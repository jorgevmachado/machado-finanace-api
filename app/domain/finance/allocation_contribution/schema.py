from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

from app.domain.finance.allocation.schema import AllocationSchema
from app.domain.finance.allocation_contribution_month.schema import (
    AllocationContributionMonthSchema,
    PayloadAllocationContributionMonthPersistSchema,
)


class PayloadAllocationContributionCreateSchema(BaseModel):
    months: list[PayloadAllocationContributionMonthPersistSchema]
    account_id: UUID
    description: str
    allocation_id: UUID
    reference_day: int | None = None
    reference_year: int
    reference_month: int | None = None
    contributor_name: str


class PayloadAllocationContributionUpdateSchema(BaseModel):
    months: list[PayloadAllocationContributionMonthPersistSchema] = []
    description: str | None = None
    reference_day: int | None = None
    reference_year: int | None = None
    reference_month: int | None = None
    contributor_name: str | None = None


class AllocationContributionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    months: list[AllocationContributionMonthSchema] = []
    account_id: UUID
    finance_id: UUID
    allocation: AllocationSchema
    description: str | None = None
    contributor_name: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
