from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.domain.finance.schema import FinanceSchema
from app.models.enums import StatusEnum


class RegisterSchema(BaseModel):
    name: str
    email: EmailStr
    username: str
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        return value


class RegisterResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    username: str
    status: StatusEnum
    created_at: datetime


class LoginSchema(BaseModel):
    credential: str
    password: str


class LoginResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    status: StatusEnum
    username: str
    finance: FinanceSchema | None = None
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
