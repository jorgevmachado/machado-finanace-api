from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService

from app.domain.finance.expense_month.repository import (
    ExpenseMonthRepository,
)
from app.domain.finance.expense_month.schema import ExpenseMonthSchema
from app.domain.finance.months.business import (
    get_month_status,
    get_paid_at,
    complete_months_in_year,
)
from app.domain.finance.months.schema import PayloadMonthPersistSchema

from app.models import (
    Expense,
    ExpenseMonth,
)

logger = logging.getLogger(__name__)


class ExpenseMonthService(BaseService[ExpenseMonthRepository, ExpenseMonth]):
    def __init__(
        self,
        repository: ExpenseMonthRepository,
    ) -> None:
        super().__init__(
            alias="ExpenseMonth",
            repository=repository,
            logger_params=LoggingParams(
                logger=logger,
                service="ExpenseMonthService",
                operation="expenseMonth",
            ),
            schema_class=ExpenseMonthSchema,
            cache_prefix="expenseMonth",
        )

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(ExpenseMonthRepository(session))

    async def persist_list(
        self,
        months: list[PayloadMonthPersistSchema],
        expense: Expense,
        reference_day: int,
        reference_year: int,
    ) -> list[ExpenseMonth]:
        persist_months = complete_months_in_year(
            months=months,
            reference_day=reference_day,
            reference_year=reference_year,
        )

        expense_months = []
        for month in persist_months:
            expense_month = await self.persist(
                month=month,
                expense=expense,
                with_throw=False,
                reference_year=reference_year,
            )
            expense_months.append(expense_month)
        return expense_months

    async def persist(
        self,
        month: PayloadMonthPersistSchema,
        expense: Expense,
        reference_year: int,
        with_throw: bool = True,
    ) -> ExpenseMonth:
        status = get_month_status(month=month)

        paid_at = get_paid_at(status, month.transaction_date)

        expense_month = await self.find_by(
            expense_id=expense.id,
            reference_year=reference_year,
            without_throw=True,
            reference_month=month.reference_month,
        )
        if expense_month:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail="Expense Month already exists",
                )
            else:
                expense_month.status = status
                expense_month.amount = month.amount
                expense_month.paid_at = paid_at
                return await self.repository.update(entity=expense_month)

        else:
            return await self.repository.save(
                entity=ExpenseMonth(
                    status=status,
                    amount=month.amount,
                    paid_at=paid_at,
                    expense_id=expense.id,
                    reference_year=reference_year,
                    reference_month=month.reference_month,
                )
            )
