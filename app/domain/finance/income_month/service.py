from __future__ import annotations

import logging
from decimal import Decimal
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.months.business import complete_months_in_year
from app.domain.finance.months.schema import PayloadMonthPersistSchema
from app.shared.utils.date import validate_received_at

from app.domain.finance.income_month.repository import (
    IncomeMonthRepository,
)
from app.domain.finance.income_month.schema import (
    IncomeMonthSchema,
)

from app.models import (
    Income,
    IncomeMonth,
)

logger = logging.getLogger(__name__)


class IncomeMonthService(BaseService[IncomeMonthRepository, IncomeMonth]):
    def __init__(
        self,
        repository: IncomeMonthRepository,
    ) -> None:
        super().__init__(
            alias="IncomeMonth",
            repository=repository,
            logger_params=LoggingParams(
                logger=logger,
                service="IncomeMonthService",
                operation="incomeMonth",
            ),
            schema_class=IncomeMonthSchema,
            cache_prefix="incomeMonth",
        )

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(IncomeMonthRepository(session))

    async def persist_list(
        self,
        months: list[PayloadMonthPersistSchema],
        income: Income,
        reference_day: int,
        reference_year: int,
    ) -> list[IncomeMonth]:

        persist_months = complete_months_in_year(
            months=months,
            reference_day=reference_day,
            reference_year=reference_year,
        )

        income_months: list[IncomeMonth] = []
        for month in persist_months:
            income_month = await self.persist(
                income=income,
                month=month,
                with_throw=False,
                reference_day=reference_day,
                reference_year=reference_year,
            )
            income_months.append(income_month)
        return income_months

    async def persist(
        self,
        month: PayloadMonthPersistSchema,
        income: Income,
        reference_day: int,
        reference_year: int,
        with_throw: bool = True,
    ) -> IncomeMonth:

        received_at = validate_received_at(
            year=reference_year,
            day=reference_day,
            month=month.reference_month,
            received_at=month.transaction_date,
        )

        income_month = await self.find_by(
            income_id=income.id,
            reference_year=reference_year,
            without_throw=True,
            reference_month=month.reference_month,
        )
        if income_month:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail="Income Month already exists",
                )
            else:
                income.amount = Decimal(str(month.amount))
                income.received_at = received_at
                return await self.repository.update(entity=income_month)

        else:
            return await self.repository.save(
                entity=IncomeMonth(
                    amount=month.amount,
                    income_id=income.id,
                    received_at=received_at,
                    reference_year=reference_year,
                    reference_month=month.reference_month,
                )
            )
