from __future__ import annotations

import logging
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.account.service import AccountService
from app.domain.finance.allocation.service import AllocationService
from app.domain.finance.allocation_contribution_month.service import (
    AllocationContributionMonthService,
)
from app.domain.finance.months.schema import PayloadMonthPersistSchema
from app.shared.utils.string import to_snake_case
from app.shared.utils.validator import validate_year
from app.domain.finance.allocation_contribution.repository import (
    AllocationContributionRepository,
)
from app.domain.finance.allocation_contribution.schema import (
    PayloadAllocationContributionCreateSchema,
    AllocationContributionSchema,
)

from app.models import AllocationContribution, Finance, Account, Allocation

logger = logging.getLogger(__name__)


class AllocationContributionService(
    BaseService[AllocationContributionRepository, AllocationContribution]
):
    def __init__(
        self,
        repository: AllocationContributionRepository,
        account_service: AccountService | None = None,
        allocation_service: AllocationService | None = None,
        allocation_contribution_month_service: AllocationContributionMonthService
        | None = None,
    ) -> None:
        super().__init__(
            alias="AllocationContribution",
            repository=repository,
            logger_params=LoggingParams(
                logger=logger,
                service="AllocationContributionService",
                operation="allocation-contribution",
            ),
            schema_class=AllocationContributionSchema,
            cache_prefix="allocation-contribution",
        )
        session = repository.session
        self.account_service = account_service or AccountService.from_session(session)
        self.allocation_service = allocation_service or AllocationService.from_session(
            session
        )
        self.allocation_contribution_month_service = (
            allocation_contribution_month_service
            or AllocationContributionMonthService.from_session(session)
        )

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(AllocationContributionRepository(session))

    async def create(
        self, finance: Finance, payload: PayloadAllocationContributionCreateSchema
    ) -> AllocationContribution:

        account, allocation = await self._validate_relations(
            finance=finance,
            account_id=payload.account_id,
            allocation_id=payload.allocation_id,
        )

        return await self.persist(
            months=payload.months,
            finance=finance,
            account=account,
            allocation=allocation,
            with_throw=True,
            description=payload.description,
            reference_day=payload.reference_day or 10,
            reference_year=payload.reference_year,
            contributor_name=payload.contributor_name,
        )

    async def _validate_relations(
        self, finance: Finance, account_id: UUID, allocation_id: UUID
    ):
        account = await self.account_service.find_by(
            id=account_id, finance_id=finance.id, without_throw=True
        )
        if not account:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Account with this id {account_id} does not exist",
            )

        allocation = await self.allocation_service.find_by(
            id=allocation_id, finance_id=finance.id, without_throw=True
        )
        if not allocation:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Allocation with this id {allocation_id} does not exist",
            )

        return account, allocation

    async def persist(
        self,
        months: list[PayloadMonthPersistSchema],
        account: Account,
        finance: Finance,
        allocation: Allocation,
        description: str,
        reference_day: int,
        reference_year: int,
        contributor_name: str,
        with_throw: bool = True,
    ) -> AllocationContribution:
        year = validate_year(reference_year)

        contributor_name_code = to_snake_case(contributor_name)

        allocation_contribution = await self.find_by(
            finance_id=finance.id,
            account_id=account.id,
            without_throw=True,
            allocation_id=allocation.id,
            reference_year=year,
            contributor_name_code=contributor_name_code,
        )

        if allocation_contribution:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Allocation Contribution with this year {year} and name {contributor_name} already exists",
                )
            else:
                allocation_contribution.description = description
                await self.allocation_contribution_month_service.persist_list(
                    months=months,
                    reference_day=reference_day,
                    reference_year=reference_year,
                    allocation_contribution=allocation_contribution,
                )
                return await self.repository.update(entity=allocation_contribution)
        else:
            created_allocation_contribution = await self.repository.save(
                entity=AllocationContribution(
                    finance_id=finance.id,
                    account_id=account.id,
                    description=description,
                    allocation_id=allocation.id,
                    contributor_name=contributor_name,
                    contributor_name_code=contributor_name_code,
                )
            )
            await self.allocation_contribution_month_service.persist_list(
                months=months,
                reference_day=reference_day,
                reference_year=reference_year,
                allocation_contribution=created_allocation_contribution,
            )

            return await self.find_by(id=created_allocation_contribution.id)
