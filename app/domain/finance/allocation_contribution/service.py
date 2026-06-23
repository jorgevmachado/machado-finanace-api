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
from app.shared.utils.date import generate_description
from app.shared.utils.validator import validate_year, validate_month
from app.domain.finance.allocation_contribution.repository import (
    AllocationContributionRepository,
)
from app.domain.finance.allocation_contribution.schema import (
    PayloadAllocationContributionCreateSchema,
    AllocationContributionSchema,
    PayloadAllocationContributionCreateListSchema,
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

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(AllocationContributionRepository(session))

    async def create(
        self, finance: Finance, payload: PayloadAllocationContributionCreateSchema
    ) -> AllocationContribution:
        payload.reference_year = validate_year(payload.reference_year)
        payload.reference_month = validate_month(payload.reference_month)

        account, allocation = await self._validate_relations(
            finance=finance,
            account_id=payload.account_id,
            allocation_id=payload.allocation_id,
        )

        return await self._persist(
            payload=payload, account=account, finance=finance, allocation=allocation
        )

    async def create_list_by_year(
        self, finance: Finance, payload: PayloadAllocationContributionCreateListSchema
    ) -> list[AllocationContribution]:
        account, allocation = await self._validate_relations(
            finance=finance,
            account_id=payload.account_id,
            allocation_id=payload.allocation_id,
        )

        payload_contributions = payload.contributions if payload.contributions else []

        if len(payload_contributions) == 0:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Allocation Contribution list cannot be empty",
            )

        allocation_contributions: list[AllocationContribution] = []
        reference_year = validate_year(payload.reference_year)
        if payload_contributions and len(payload_contributions) > 0:
            for item in payload_contributions:
                reference_month = validate_month(item.reference_month)

                description = generate_description(
                    month=item.reference_month,
                    source=item.contributor_name,
                    description=payload.description,
                    item_description=item.description,
                )

                item_payload = PayloadAllocationContributionCreateSchema(
                    amount=item.amount,
                    account_id=account.id,
                    allocation_id=allocation.id,
                    reference_year=reference_year,
                    reference_month=reference_month,
                    contributor_name=item.contributor_name,
                    description=description,
                )

                allocation_contribution = await self._persist(
                    payload=item_payload,
                    account=account,
                    finance=finance,
                    allocation=allocation,
                    with_throw=False,
                )
                allocation_contributions.append(allocation_contribution)
        return allocation_contributions

    async def _persist(
        self,
        payload: PayloadAllocationContributionCreateSchema,
        account: Account,
        finance: Finance,
        allocation: Allocation,
        with_throw: bool = True,
    ) -> AllocationContribution:
        reference_year = validate_year(payload.reference_year)
        reference_month = validate_month(payload.reference_month)

        allocation_contribution = await self.find_by(
            finance_id=finance.id,
            account_id=account.id,
            allocation_id=allocation.id,
            reference_year=reference_year,
            contributor_name=payload.contributor_name,
            reference_month=reference_month,
            without_throw=True,
        )

        if allocation_contribution:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Allocation Contribution with this year {reference_year}, month {reference_month} and name {payload.contributor_name} already exists",
                )
            else:
                allocation_contribution.amount = payload.amount
                return await self.repository.update(entity=allocation_contribution)
        else:
            return await self.repository.save(
                entity=AllocationContribution(
                    amount=payload.amount,
                    finance_id=finance.id,
                    account_id=account.id,
                    description=payload.description,
                    allocation_id=allocation.id,
                    reference_year=reference_year,
                    reference_month=reference_month,
                    contributor_name=payload.contributor_name,
                )
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
