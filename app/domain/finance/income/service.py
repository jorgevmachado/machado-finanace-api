from __future__ import annotations

import logging
from http import HTTPStatus
from typing import cast

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
    PayloadIncomePersistSchema, PayloadIncomeUpdateSchema,
)

from app.models import Income, Finance, Account, utcnow
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

        account = await self.account_service.find_by(
            id=payload.account_id, finance_id=finance.id, without_throw=True
        )

        if not account:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Account with this id {payload.account_id} does not exist",
            )

        return await self.persist(
            months=payload.months,
            source=payload.source,
            account=account,
            with_throw=True,
            description=payload.description,
            reference_day=payload.reference_day or 10,
            reference_year=payload.reference_year,
        )

    async def update(self, param: str, payload: PayloadIncomeUpdateSchema, **kwargs) -> Income:
        finance_id = kwargs.get("finance_id") if kwargs else None
        finance_id = cast(str, finance_id) if finance_id else None
        reference_year = payload.reference_year if payload.reference_year else utcnow().year
        entity = await self.find_one(param=param)
        has_change = False
        account = entity.account

        if payload.account_id and payload.account_id != account.id:
            has_change = True
            account = await self.account_service.find_by(
                id=payload.account_id, finance_id=finance_id, without_throw=True
            )
            if not account:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Account with this id {payload.account_id} does not exist",
                )
        if payload.source and payload.source != entity.source:
            has_change = True
            source_code = to_snake_case(payload.source or '')
            existing_income = await self.find_by(
                account_id=account.id,
                source_code=source_code,
                without_throw=True,
            )
            if existing_income:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Income with this year {reference_year} and source {payload.source} already exists",
                )
            entity.source = payload.source
            entity.source_code = source_code

        if payload.description and payload.description !=  entity.description:
            has_change = True
            entity.description = payload.description

        if payload.months and len(payload.months) > 0:
            has_change = True
            payload_months = [
                PayloadMonthPersistSchema(
                    amount=month.amount,
                    reference_day=payload.reference_day or 10,
                    reference_month=month.reference_month,
                    transaction_date=month.transaction_date,
                )
                for month in payload.months
            ]
            await self.income_month_service.persist_list(
                income=entity,
                months=payload_months,
                reference_day=payload.reference_day or 10,
                reference_year=reference_year,
            )

        if not has_change:
            return entity
        await self.cache_service.delete_domain()
        return await self.repository.update(entity=entity)

    async def persist(
        self,
        months: list[PayloadMonthPersistSchema],
        source: str,
        account: Account,
        description: str,
        reference_day: int,
        reference_year: int,
        with_throw: bool = True,
    ) -> Income:

        year = validate_year(reference_year)

        source_code = to_snake_case(source)

        income = await self.find_by(
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
                    account_id=account.id,
                    source_code=source_code,
                    description=description,
                )
            )
            months = await self.income_month_service.persist_list(
                income=created_income,
                months=months,
                reference_day=reference_day,
                reference_year=year,
            )
            updated_income = await self.find_by(id=created_income.id)
            updated_income.months = months
            return updated_income

    async def persist_list(
        self,
        account: Account,
        payloads: list[PayloadIncomePersistSchema],
        reference_year: int,
        with_throw: bool = True,
        reference_day: int = 10,
    ) -> list[Income]:
        incomes: list[Income] = []
        for payload in payloads:
            income = await self.persist(
                months=payload.months,
                source=payload.source,
                account=account,
                with_throw=with_throw,
                description=payload.description,
                reference_day=reference_day,
                reference_year=reference_year,
            )
            incomes.append(income)
        return incomes
