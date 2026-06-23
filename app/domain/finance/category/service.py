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
    PayloadCategoryCreateListSchema,
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

    async def create_list(
        self,
        finance: Finance,
        payload: PayloadCategoryCreateListSchema,
    ) -> list[Category]:
        payload_categories = payload.categories if payload.categories else []

        if len(payload_categories) == 0:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Categories list cannot be empty",
            )

        categories: list[Category] = []

        if payload_categories and len(payload_categories) > 0:
            for item in payload_categories:
                category = await self.persist(
                    finance=finance,
                    payload=item,
                    with_throw=False,
                )
                categories.append(category)

        return categories

    async def persist(
        self,
        finance: Finance,
        payload: PayloadCategoryCreateSchema,
        with_throw: bool = True,
    ) -> Category:
        name_code = to_snake_case(payload.name)
        category = await self.find_by(
            finance_id=finance.id, name_code=name_code, without_throw=True
        )
        if category:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Category with this name {payload.name} already exists",
                )
            else:
                return category
        else:
            return await self.repository.save(
                entity=Category(
                    finance_id=finance.id,
                    name=payload.name,
                    name_code=name_code,
                    type=payload.type,
                    description=payload.description,
                )
            )
