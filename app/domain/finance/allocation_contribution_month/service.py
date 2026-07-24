from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.allocation_contribution_month.repository import (
    AllocationContributionMonthRepository,
)
from app.domain.finance.allocation_contribution_month.schema import (
    AllocationContributionMonthSchema,
)
from app.domain.finance.months.business import complete_months_in_year
from app.domain.finance.months.schema import PayloadMonthPersistSchema
from app.models import AllocationContribution, AllocationContributionMonth
from app.shared.utils.date import validate_received_at

logger = logging.getLogger(__name__)


class AllocationContributionMonthService(
    BaseService[AllocationContributionMonthRepository, AllocationContributionMonth]
):
    def __init__(
        self,
        repository: AllocationContributionMonthRepository,
    ) -> None:
        super().__init__(
            alias="AllocationContributionMonth",
            repository=repository,
            logger_params=LoggingParams(
                logger=logger,
                service="AllocationContributionMonthService",
                operation="allocationContributionMonth",
            ),
            schema_class=AllocationContributionMonthSchema,
            cache_prefix="allocationContributionMonth",
        )

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(AllocationContributionMonthRepository(session))

    async def persist_list(
        self,
        months: list[PayloadMonthPersistSchema],
        reference_day: int,
        reference_year: int,
        allocation_contribution: AllocationContribution,
    ) -> list[AllocationContributionMonth]:
        persist_months = complete_months_in_year(
            months=months,
            reference_day=reference_day,
            reference_year=reference_year,
        )

        allocation_contribution_months: list[AllocationContributionMonth] = []

        for month in persist_months:
            allocation_contribution_month = await self.persist(
                month=month,
                with_throw=False,
                reference_day=reference_day,
                reference_year=reference_year,
                allocation_contribution=allocation_contribution,
            )
            allocation_contribution_months.append(allocation_contribution_month)

        return allocation_contribution_months

    async def persist(
        self,
        month: PayloadMonthPersistSchema,
        reference_day: int,
        reference_year: int,
        allocation_contribution: AllocationContribution,
        with_throw: bool = True,
    ) -> AllocationContributionMonth:

        received_at = validate_received_at(
            day=reference_day,
            year=reference_year,
            month=month.reference_month,
            received_at=month.transaction_date,
        )

        allocation_contribution_month = await self.find_by(
            without_throw=True,
            reference_year=reference_year,
            reference_month=month.reference_month,
            allocation_contribution_id=allocation_contribution.id,
        )

        if allocation_contribution_month:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Allocation Contribution Month with this year {reference_year}, month {month.reference_month} already exists",
                )
            else:
                allocation_contribution_month.amount = month.amount
                allocation_contribution_month.received_at = received_at
                return await self.repository.update(
                    entity=allocation_contribution_month
                )
        else:
            return await self.repository.save(
                entity=AllocationContributionMonth(
                    amount=month.amount,
                    received_at=received_at,
                    reference_year=reference_year,
                    reference_month=month.reference_month,
                    allocation_contribution_id=allocation_contribution.id,
                )
            )
