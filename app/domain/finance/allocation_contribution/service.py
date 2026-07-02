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
from app.domain.finance.allocation_contribution_month.schema import (
    PayloadAllocationContributionMonthPersistSchema,
)
from app.domain.finance.allocation_contribution_month.service import (
    AllocationContributionMonthService,
)
from app.domain.finance.business import merge_months_by_reference_month
from app.domain.finance.schema import FinanceCreateContributionsSchema
from app.shared.utils.date import get_received_at
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
            payload=payload, account=account, finance=finance, allocation=allocation
        )

    async def persist(
        self,
        payload: PayloadAllocationContributionCreateSchema,
        account: Account,
        finance: Finance,
        allocation: Allocation,
        with_throw: bool = True,
    ) -> AllocationContribution:
        reference_year = validate_year(payload.reference_year)

        allocation_contribution = await self.find_by(
            finance_id=finance.id,
            account_id=account.id,
            allocation_id=allocation.id,
            reference_year=reference_year,
            contributor_name=payload.contributor_name,
            without_throw=True,
        )

        if allocation_contribution:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Allocation Contribution with this year {reference_year} and name {payload.contributor_name} already exists",
                )
            else:
                allocation_contribution.description = payload.description
                await self.allocation_contribution_month_service.persist_list(
                    payload=payload.months,
                    reference_day=payload.reference_day or 10,
                    reference_year=reference_year,
                    allocation_contribution=allocation_contribution,
                )
                return await self.repository.update(entity=allocation_contribution)
        else:
            created_allocation_contribution = await self.repository.save(
                entity=AllocationContribution(
                    finance_id=finance.id,
                    account_id=account.id,
                    description=payload.description,
                    allocation_id=allocation.id,
                    contributor_name=payload.contributor_name,
                )
            )
            await self.allocation_contribution_month_service.persist_list(
                payload=payload.months,
                reference_day=payload.reference_day or 10,
                reference_year=reference_year,
                allocation_contribution=created_allocation_contribution,
            )

            return await self.find_by(id=created_allocation_contribution.id)

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

    async def create_by_account(
        self,
        finance: Finance,
        account: Account,
        allocation: Allocation,
        reference_day: int,
        reference_year: int,
        payload_allocation_contributions: list[FinanceCreateContributionsSchema],
    ) -> list[AllocationContribution]:
        allocation_contributions: list[AllocationContribution] = []
        if len(payload_allocation_contributions) > 0:
            for payload_contribution in payload_allocation_contributions:
                payload_contribution_description = payload_contribution.description
                payload_contribution_months = merge_months_by_reference_month(
                    payload_contribution.months or []
                )

                months: list[PayloadAllocationContributionMonthPersistSchema] = []
                if len(payload_contribution_months) > 0:
                    for payload_contribution_month in payload_contribution_months:
                        received_at = get_received_at(
                            year=reference_year,
                            month=payload_contribution_month.reference_month,
                            day=payload_contribution_month.reference_day
                            or reference_day,
                        )
                        month = PayloadAllocationContributionMonthPersistSchema(
                            id=payload_contribution_month.id,
                            amount=payload_contribution_month.amount,
                            received_at=received_at,
                            reference_day=payload_contribution_month.reference_day,
                            reference_year=payload_contribution_month.reference_year,
                            reference_month=payload_contribution_month.reference_month,
                        )
                        months.append(month)

                allocation_contribution = await self.persist(
                    finance=finance,
                    account=account,
                    payload=PayloadAllocationContributionCreateSchema(
                        months=months,
                        account_id=account.id,
                        description=payload_contribution_description
                        or payload_contribution.contributor_name,
                        allocation_id=allocation.id,
                        reference_day=reference_day,
                        reference_year=reference_year,
                        contributor_name=payload_contribution.contributor_name,
                    ),
                    allocation=allocation,
                    with_throw=False,
                )
                allocation_contributions.append(allocation_contribution)

        return allocation_contributions
