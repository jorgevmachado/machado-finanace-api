from __future__ import annotations

import logging
from datetime import date
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.account.service import AccountService
from app.shared.utils.date import generate_description, get_valid_day
from app.shared.utils.validator import validate_year, validate_month
from app.domain.finance.income.repository import IncomeRepository
from app.domain.finance.income.schema import (
    PayloadIncomeCreateSchema,
    IncomeSchema,
    PayloadIncomeCreateListSchema,
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

    async def create_list_by_year(
        self, finance: Finance, payload: PayloadIncomeCreateListSchema
    ) -> list[Income]:
        account = await self._validate_relations(
            finance=finance, account_id=payload.account_id
        )

        payload_incomes = payload.incomes if payload.incomes else []
        if len(payload_incomes) == 0 or len(payload_incomes) > 12:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Incomes must be between 1 and 12",
            )

        incomes: list[Income] = []
        reference_year = validate_year(payload.reference_year)
        if payload_incomes and len(payload_incomes) > 0:
            for item in payload_incomes:
                reference_month = validate_month(item.reference_month)
                reference_day = get_valid_day(
                    year=reference_year,
                    month=reference_month,
                    day=payload.reference_day,
                )
                received_at = date(reference_year, reference_month, reference_day)

                description = generate_description(
                    month=item.reference_month,
                    source=payload.source,
                    description=payload.description,
                    item_description=item.description,
                )

                item_payload = PayloadIncomeCreateSchema(
                    source=payload.source,
                    amount=item.amount,
                    account_id=account.id,
                    received_at=received_at,
                    description=description,
                    reference_year=reference_year,
                    reference_month=reference_month,
                )

                income = await self._persist(
                    payload=item_payload,
                    account=account,
                    finance=finance,
                    with_throw=False,
                )

                incomes.append(income)
        return incomes

    async def _validate_relations(
        self, account_id: UUID, finance: Finance
    ):
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
                income.amount = payload.amount
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
