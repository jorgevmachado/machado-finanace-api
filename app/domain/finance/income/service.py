from __future__ import annotations

import logging
from decimal import Decimal
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.account.service import AccountService
from app.domain.finance.business import merge_months_by_reference_month
from app.domain.finance.income.business import get_received_at
from app.domain.finance.schema import FinanceCreateIncomeSchema
from app.shared.utils.date import generate_description
from app.shared.utils.validator import validate_year, validate_month
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

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(IncomeRepository(session))

    async def create(
        self, finance: Finance, payload: PayloadIncomeCreateSchema
    ) -> Income:
        account = await self._validate_relations(
            finance=finance, account_id=payload.account_id
        )

        payload.reference_year = validate_year(payload.reference_year)
        payload.reference_month = validate_month(payload.reference_month)

        return await self._persist(payload, account, finance)

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
        reference_month = validate_month(payload.reference_month)

        source_code = to_snake_case(payload.source)

        income = await self.find_by(
            finance_id=finance.id,
            account_id=account.id,
            source_code=source_code,
            reference_year=reference_year,
            reference_month=reference_month,
            without_throw=True,
        )

        if income:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Income with this year {reference_year}, month {reference_month} and source {payload.source} already exists",
                )
            else:
                income.amount = Decimal(str(payload.amount))
                return await self.repository.update(entity=income)
        else:
            return await self.repository.save(
                entity=Income(
                    source=payload.source,
                    amount=payload.amount,
                    finance_id=finance.id,
                    account_id=account.id,
                    source_code=source_code,
                    received_at=payload.received_at,
                    description=payload.description,
                    reference_year=reference_year,
                    reference_month=reference_month,
                )
            )

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
                if len(payload_income_months) > 0:
                    for payload_income_month in payload_income_months:
                        received_at = get_received_at(
                            year=reference_year,
                            month=payload_income_month.reference_month,
                            day=payload_income_month.reference_day or reference_day,
                        )
                        description = generate_description(
                            month=payload_income_month.reference_month,
                            source=payload_income_source,
                            description=payload_income_description,
                        )

                        await self._persist(
                            finance=finance,
                            account=account,
                            payload=PayloadIncomeCreateSchema(
                                source=payload_income_source,
                                amount=payload_income_month.amount,
                                account_id=account.id,
                                received_at=received_at,
                                description=description,
                                reference_year=reference_year,
                                reference_month=payload_income_month.reference_month,
                            ),
                            with_throw=False,
                        )
        return incomes
