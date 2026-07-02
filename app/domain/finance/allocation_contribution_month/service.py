from __future__ import annotations

import logging
from datetime import date
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
    PayloadAllocationContributionMonthPersistSchema,
)
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
        payload: list[PayloadAllocationContributionMonthPersistSchema],
        reference_day: int,
        reference_year: int,
        allocation_contribution: AllocationContribution,
    ) -> list[AllocationContributionMonth]:
        print("# => persist_list => payload => len => ", len(payload))
        months_provided = {item.reference_month for item in payload}
        all_months = set(range(1, 13))
        missing_months = all_months - months_provided

        for month in missing_months:
            payload.append(
                PayloadAllocationContributionMonthPersistSchema(
                    amount=0.0,
                    received_at=date(reference_year, month, reference_day),
                    reference_month=month,
                )
            )

        payload.sort(key=lambda x: x.reference_month)

        allocation_contribution_months: list[AllocationContributionMonth] = []

        for item in payload:
            allocation_contribution_month = await self.persist(
                payload=item,
                with_throw=False,
                reference_day=reference_day,
                reference_year=reference_year,
                allocation_contribution=allocation_contribution,
            )
            allocation_contribution_months.append(allocation_contribution_month)

        return allocation_contribution_months

    async def persist(
        self,
        reference_day: int,
        reference_year: int,
        allocation_contribution: AllocationContribution,
        payload: PayloadAllocationContributionMonthPersistSchema,
        with_throw: bool = True,
    ) -> AllocationContributionMonth:

        current_reference_year = payload.reference_year or reference_year

        received_at = validate_received_at(
            year=current_reference_year,
            day=reference_day,
            month=payload.reference_month,
            received_at=payload.received_at,
        )

        allocation_contribution_month = await self.find_by(
            without_throw=True,
            reference_year=current_reference_year,
            reference_month=payload.reference_month,
            allocation_contribution_id=allocation_contribution.id,
        )

        if allocation_contribution_month:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Allocation Contribution Month with this year {current_reference_year}, month {payload.reference_month} already exists",
                )
            else:
                allocation_contribution_month.amount = payload.amount
                allocation_contribution_month.received_at = received_at
                return await self.repository.update(
                    entity=allocation_contribution_month
                )
        else:
            return await self.repository.save(
                entity=AllocationContributionMonth(
                    amount=payload.amount,
                    received_at=received_at,
                    reference_year=current_reference_year,
                    reference_month=payload.reference_month,
                    allocation_contribution_id=allocation_contribution.id,
                )
            )
