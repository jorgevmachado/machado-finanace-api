from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.income_month.business import validate_received_at

from app.domain.finance.income_month.repository import (
    IncomeMonthRepository,
)
from app.domain.finance.income_month.schema import (
    IncomeMonthSchema,
    PayloadIncomeMonthPersistSchema,
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
        income: Income,
        reference_day: int,
        reference_year: int,
        payload: list[PayloadIncomeMonthPersistSchema],
    ) -> list[IncomeMonth]:
        months_provided = {item.reference_month for item in payload}
        all_months = set(range(1, 13))
        missing_months = all_months - months_provided

        # Create missing months with default values
        for month in missing_months:
            payload.append(
                PayloadIncomeMonthPersistSchema(
                    reference_month=month,
                    amount=0.0,
                    received_at=date(reference_year, month, reference_day),
                )
            )

        # Sort by month for consistency
        payload.sort(key=lambda x: x.reference_month)

        income_months = []
        for item in payload:
            income_month = await self.persist(
                income=income,
                payload=item,
                with_throw=False,
                reference_day=reference_day,
                reference_year=reference_year,
            )
            income_months.append(income_month)
        return income_months

    async def persist(
        self,
        income: Income,
        payload: PayloadIncomeMonthPersistSchema,
        reference_year: int,
        reference_day: int,
        with_throw: bool = True,
    ) -> IncomeMonth:

        current_reference_year = payload.reference_year or reference_year
        
        received_at = validate_received_at(
            year=current_reference_year,
            day=reference_day,
            month=payload.reference_month,
            received_at=payload.received_at
        )

        income_month = await self.find_by(
            income_id=income.id,
            reference_year=current_reference_year,
            reference_month=payload.reference_month,
            without_throw=True,
        )
        if income_month:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail="Income Month already exists",
                )
            else:
                income.amount = Decimal(str(payload.amount))
                income.received_at = received_at
                return await self.repository.update(entity=income_month)

        else:
            return await self.repository.save(
                entity=IncomeMonth(
                    amount=payload.amount,
                    income_id=income.id,
                    received_at=received_at,
                    reference_year=current_reference_year,
                    reference_month=payload.reference_month,
                )
            )
