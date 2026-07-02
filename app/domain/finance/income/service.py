from __future__ import annotations

import logging
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.account.service import AccountService
from app.domain.finance.business import merge_months_by_reference_month
from app.domain.finance.income.business import get_received_at
from app.domain.finance.income_month.schema import PayloadIncomeMonthPersistSchema
from app.domain.finance.income_month.service import IncomeMonthService
from app.domain.finance.schema import FinanceCreateIncomeSchema
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
        self.income_month_service = income_month_service or IncomeMonthService.from_session(session)

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(IncomeRepository(session))

    async def create(
        self, finance: Finance, payload: PayloadIncomeCreateSchema
    ) -> Income:
        account = await self._validate_relations(
            finance=finance, account_id=payload.account_id
        )

        return await self._persist(payload, account, finance,True)

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

    async def _persist(
        self,
        payload: PayloadIncomeCreateSchema,
        account: Account,
        finance: Finance,
        with_throw: bool = True,
    ) -> Income:

        reference_year = validate_year(payload.reference_year)

        source_code = to_snake_case(payload.source)

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
                    detail=f"Income with this year {reference_year} and source {payload.source} already exists",
                )
            else:
                income.description = payload.description
                await self.income_month_service.persist_list(
                    income=income,
                    reference_year=reference_year,
                    reference_day=payload.reference_day or 10,
                    payload=payload.months,
                )
                return await self.repository.update(entity=income)
        else:
            created_income = await self.repository.save(
                entity=Income(
                    source=payload.source,
                    finance_id=finance.id,
                    account_id=account.id,
                    source_code=source_code,
                    description=payload.description,
                )
            )
            await self.income_month_service.persist_list(
                income=created_income,
                reference_year=reference_year,
                reference_day=payload.reference_day or 10,
                payload=payload.months,
            )
            return await self.find_by(id=created_income.id)

    async def create_by_account(
        self,
        finance: Finance,
        account: Account,
        reference_day: int,
        reference_year: int,
        payload_incomes: list[FinanceCreateIncomeSchema],
    ) -> list[Income]:
        incomes: list[Income] = []
        if len(payload_incomes) > 0:
            for payload_income in payload_incomes:
                payload_income_source = payload_income.source
                payload_income_description = payload_income.description
                payload_income_months = merge_months_by_reference_month(
                    months=payload_income.months or []
                )
                months: list[PayloadIncomeMonthPersistSchema] = []
                if len(payload_income_months) > 0:
                    for payload_income_month in payload_income_months:
                        received_at = get_received_at(
                            year=reference_year,
                            month=payload_income_month.reference_month,
                            day=payload_income_month.reference_day or reference_day,
                        )
                        month = PayloadIncomeMonthPersistSchema(
                            id=payload_income_month.id,
                            amount=payload_income_month.amount,
                            received_at=received_at,
                            reference_day=payload_income_month.reference_day,
                            reference_year=payload_income_month.reference_year,
                            reference_month=payload_income_month.reference_month,
                        )
                        months.append(month)

                income = await self._persist(
                    payload=PayloadIncomeCreateSchema(
                        months=months,
                        source=payload_income_source,
                        account_id=account.id,
                        description=payload_income_description or payload_income_source,
                        reference_year=reference_year,
                        reference_day=reference_day,
                    ),
                    account=account,
                    finance=finance,
                    with_throw=False,
                )
                incomes.append(income)
        return incomes
