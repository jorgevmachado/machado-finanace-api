from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.allocation.repository import AllocationRepository
from app.domain.finance.allocation.schema import PayloadAllocationCreateSchema, AllocationSchema

from app.models import (
    User,
    Allocation
)
from app.shared.utils.string import to_snake_case

logger = logging.getLogger(__name__)


class AllocationService(BaseService[AllocationRepository, Allocation]):
    def __init__(
        self,
        repository: AllocationRepository,
    ) -> None:
        super().__init__(
            alias="Allocation",
            repository=repository,
            logger_params=LoggingParams(
                logger=logger, service="AllocationService", operation="allocation"
            ),
            schema_class=AllocationSchema,
            cache_prefix="allocation",
        )

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(AllocationRepository(session))

    async def create(self, current_user: User, payload: PayloadAllocationCreateSchema) -> Allocation:
        if not current_user.finance:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="User must be onboarded first",
            )
        allocation = await self.find_by(finance_id=current_user.finance.id, name=payload.name, without_throw=True)
        if allocation:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Allocation with this name already exists",
            )
        name_code = to_snake_case(payload.name)
        return await self.repository.save(
            entity=Allocation(
                finance_id=current_user.finance.id,
                name=payload.name,
                name_code=name_code,
                type=payload.type,
                is_active=True,
                description=payload.description,
            )
        )
