from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.category.repository import CategoryRepository
from app.domain.finance.category.schema import (
    PayloadCategoryCreateSchema,
    CategorySchema,
)
from app.shared.utils.string import to_snake_case

from app.models import User, Category

logger = logging.getLogger(__name__)


class CategoryService(BaseService[CategoryRepository, Category]):
    def __init__(
        self,
        repository: CategoryRepository,
    ) -> None:
        super().__init__(
            alias="Category",
            repository=repository,
            logger_params=LoggingParams(
                logger=logger, service="CategoryService", operation="category"
            ),
            schema_class=CategorySchema,
            cache_prefix="category",
        )

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(CategoryRepository(session))

    async def create(
        self, current_user: User, payload: PayloadCategoryCreateSchema
    ) -> Category:
        if not current_user.finance:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="User must be onboarded first",
            )
        name_code = to_snake_case(payload.name)
        category = await self.find_by(
            finance_id=current_user.finance.id, name_code=name_code, without_throw=True
        )
        if category:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Category with this name {payload.name} already exists",
            )

        return await self.repository.save(
            entity=Category(
                finance_id=current_user.finance.id,
                name=payload.name,
                name_code=name_code,
                type=payload.type,
                description=payload.description,
            )
        )
