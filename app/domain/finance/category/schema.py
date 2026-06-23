from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

from app.models import CategoryTypeEnum


class PayloadCategoryCreateSchema(BaseModel):
    name: str
    type: CategoryTypeEnum
    description: str


class PayloadCategoryCreateListSchema(BaseModel):
    categories: list[PayloadCategoryCreateSchema]


class PayloadCategoryUpdateSchema(BaseModel):
    name: str | None = None
    type: CategoryTypeEnum | None = None
    description: str | None = None


class CategorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    type: CategoryTypeEnum
    name_code: str
    finance_id: UUID
    description: str
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
