from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class PayloadAllocationContributionCreateSchema(BaseModel):    
    amount: float
    account_id: UUID
    description: str
    allocation_id: UUID
    reference_year: int
    reference_month: int
    contributor_name: str

class PayloadAllocationContributionUpdateSchema(BaseModel):    
    amount: float | None = None
    description: str | None = None
    reference_year: int | None = None
    reference_month: int | None = None
    contributor_name: str | None = None

class AllocationContributionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    amount: float
    account_id: UUID
    finance_id: UUID
    allocation_id: UUID
    description: str | None = None    
    reference_year: int
    reference_month: int
    contributor_name: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

