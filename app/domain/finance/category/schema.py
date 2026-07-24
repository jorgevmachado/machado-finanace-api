from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class PayloadCategoryCreateSchema(BaseModel):
    name: str
    description: str


class PayloadCategoryUpdateSchema(BaseModel):
    name: str | None = None
    description: str | None = None


class CategorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    name_code: str
    finance_id: UUID
    description: str
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
