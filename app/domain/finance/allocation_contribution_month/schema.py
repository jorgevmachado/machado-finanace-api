from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, BaseModel


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
