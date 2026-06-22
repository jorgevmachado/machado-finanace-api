from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.account.service import AccountService
from app.domain.finance.allocation.service import AllocationService
from app.shared.utils.validator import validate_year, validate_month
from app.domain.finance.allocation_contribution.repository import AllocationContributionRepository
from app.domain.finance.allocation_contribution.schema import PayloadAllocationContributionCreateSchema, AllocationContributionSchema

from app.models import User, AllocationContribution

logger = logging.getLogger(__name__)


class AllocationContributionService(BaseService[AllocationContributionRepository, AllocationContribution]):
    def __init__(
        self,
        repository: AllocationContributionRepository,
        account_service: AccountService | None = None,
        allocation_service: AllocationService | None = None,
    ) -> None:
        super().__init__(
            alias="AllocationContribution",
            repository=repository,
            logger_params=LoggingParams(
                logger=logger, service="AllocationContributionService", operation="allocation-contribution"
            ),
            schema_class=AllocationContributionSchema,
            cache_prefix="allocation-contribution",
        )
        session = repository.session
        self.account_service = account_service or AccountService.from_session(session)
        self.allocation_service = allocation_service or AllocationService.from_session(session)

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(AllocationContributionRepository(session))

    async def create(self, current_user: User, payload: PayloadAllocationContributionCreateSchema) -> AllocationContribution:
        if not current_user.finance:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="User must be onboarded first",
            )

        reference_year = validate_year(payload.reference_year)
        reference_month = validate_month(payload.reference_month)

        allocation_contribution = await self.find_by(
            finance_id=current_user.finance.id,
            contributor_name=payload.contributor_name,
            reference_year=reference_year,
            reference_month=reference_month,
            without_throw=True
        )
        if allocation_contribution:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Allocation Contribution with this year {reference_year}, month {reference_month} and name {payload.contributor_name} already exists",
            )

        account = await self.account_service.find_by(id=payload.account_id, without_throw=True)
        if not account:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Account with this id {payload.account_id} does not exist",
            )

        allocation = await self.allocation_service.find_by(
            id=payload.allocation_id, without_throw=True
        )
        if not allocation:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Allocation with this id {payload.allocation_id} does not exist",
            )
        return await self.repository.save(
            entity=AllocationContribution(
                amount=payload.amount,
                finance_id=current_user.finance.id,
                account_id=account.id,
                description=payload.description,
                allocation_id=allocation.id,
                reference_year=reference_year,
                reference_month=reference_month,
                contributor_name=payload.contributor_name
            )
        )    
