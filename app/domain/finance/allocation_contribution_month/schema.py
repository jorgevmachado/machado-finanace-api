from datetime import date, datetime
from uuid import UUID

from pydantic import ConfigDict, BaseModel


class PayloadAllocationContributionMonthPersistSchema(BaseModel):
    id: UUID | None = None
    amount: float
    received_at: date | None = None
    reference_day: int | None = None
    reference_year: int | None = None
    reference_month: int


class AllocationContributionMonthSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    amount: float
    reference_year: int
    reference_month: int
    allocation_contribution_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
