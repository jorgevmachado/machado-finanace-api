from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.account.service import AccountService
from app.domain.finance.allocation.repository import AllocationRepository
from app.domain.finance.allocation.schema import (
    PayloadAllocationCreateSchema,
    AllocationSchema,
)

from app.models import Allocation, Finance, Account
from app.shared.utils.string import to_snake_case

logger = logging.getLogger(__name__)


class AllocationService(BaseService[AllocationRepository, Allocation]):
    def __init__(
        self,
        repository: AllocationRepository,
        account_service: AccountService | None = None,
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
        session = repository.session
        self.account_service = account_service or AccountService.from_session(session)

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(AllocationRepository(session))

    async def create(
        self,
        finance: Finance,
        payload: PayloadAllocationCreateSchema,
    ) -> Allocation:

        account = await self.account_service.find_by(
            id=payload.account_id, finance_id=finance.id, without_throw=True
        )

        if not account:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Account with this id {payload.account_id} does not exist",
            )

        return await self.persist(
            name=payload.name, account=account, description=payload.description
        )

    async def persist(
        self,
        name: str,
        account: Account,
        description: str,
        with_throw: bool = True,
    ) -> Allocation:

        name_code = to_snake_case(name)

        allocation = await self.find_by(
            name_code=name_code, account_id=account.id, without_throw=True
        )
        if allocation:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Allocation with this name {name} already exists",
                )
            else:
                return allocation
        else:
            return await self.repository.save(
                entity=Allocation(
                    name=name,
                    name_code=name_code,
                    is_active=True,
                    account_id=account.id,
                    description=description,
                )
            )
