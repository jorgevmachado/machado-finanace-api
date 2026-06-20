from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class FinanceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
