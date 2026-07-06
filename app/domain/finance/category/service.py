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

from app.models import Category, Finance

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
        self,
        finance: Finance,
        payload: PayloadCategoryCreateSchema,
    ) -> Category:
        return await self.persist(
            name=payload.name,
            finance=finance,
            description=payload.description,
        )

    async def persist(
        self,
        name: str,
        finance: Finance,
        description: str,
        with_throw: bool = True,
    ) -> Category:
        name_code = to_snake_case(name)
        category = await self.find_by(
            finance_id=finance.id, name_code=name_code, without_throw=True
        )
        if category:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Category with this name {name} already exists",
                )
            else:
                return category
        else:
            return await self.repository.save(
                entity=Category(
                    name=name,
                    name_code=name_code,
                    finance_id=finance.id,
                    description=description,
                )
            )
