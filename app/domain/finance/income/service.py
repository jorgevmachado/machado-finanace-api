from __future__ import annotations

import logging
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.account.service import AccountService
from app.domain.finance.income_month.service import IncomeMonthService
from app.domain.finance.months.schema import PayloadMonthPersistSchema
from app.shared.utils.validator import validate_year
from app.domain.finance.income.repository import IncomeRepository
from app.domain.finance.income.schema import (
    PayloadIncomeCreateSchema,
    IncomeSchema,
)

from app.models import Income, Finance, Account
from app.shared.utils.string import to_snake_case

logger = logging.getLogger(__name__)


class IncomeService(BaseService[IncomeRepository, Income]):
    def __init__(
        self,
        repository: IncomeRepository,
        account_service: AccountService | None = None,
        income_month_service: IncomeMonthService | None = None,
    ) -> None:
        super().__init__(
            alias="Income",
            repository=repository,
            logger_params=LoggingParams(
                logger=logger, service="IncomeService", operation="income"
            ),
            schema_class=IncomeSchema,
            cache_prefix="income",
        )
        session = repository.session
        self.account_service = account_service or AccountService.from_session(session)
        self.income_month_service = (
            income_month_service or IncomeMonthService.from_session(session)
        )

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(IncomeRepository(session))

    async def create(
        self, finance: Finance, payload: PayloadIncomeCreateSchema
    ) -> Income:

        account = await self._validate_relations(
            finance=finance, account_id=payload.account_id
        )

        return await self.persist(
            months=payload.months,
            source=payload.source,
            finance=finance,
            account=account,
            with_throw=True,
            description=payload.description,
            reference_day=payload.reference_day or 10,
            reference_year=payload.reference_year,
        )

    async def _validate_relations(self, account_id: UUID, finance: Finance):
        account = await self.account_service.find_by(
            id=account_id, finance_id=finance.id, without_throw=True
        )

        if not account:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Account with this id {account_id} does not exist",
            )

        return account

    async def persist(
        self,
        months: list[PayloadMonthPersistSchema],
        source: str,
        finance: Finance,
        account: Account,
        description: str,
        reference_day: int,
        reference_year: int,
        with_throw: bool = True,
    ) -> Income:

        year = validate_year(reference_year)

        source_code = to_snake_case(source)

        income = await self.find_by(
            finance_id=finance.id,
            account_id=account.id,
            source_code=source_code,
            without_throw=True,
        )

        if income:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Income with this year {year} and source {source} already exists",
                )
            else:
                income.description = description
                await self.income_month_service.persist_list(
                    income=income,
                    months=months,
                    reference_year=year,
                    reference_day=reference_day,
                )
                return await self.repository.update(entity=income)
        else:
            created_income = await self.repository.save(
                entity=Income(
                    source=source,
                    finance_id=finance.id,
                    account_id=account.id,
                    source_code=source_code,
                    description=description,
                )
            )
            await self.income_month_service.persist_list(
                income=created_income,
                months=months,
                reference_day=reference_day,
                reference_year=year,
            )
            return await self.find_by(id=created_income.id)
