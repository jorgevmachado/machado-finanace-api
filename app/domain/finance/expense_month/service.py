from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.expense_month.business import get_status, validate_paid_at

from app.domain.finance.expense_month.repository import (
    ExpenseMonthRepository,
)
from app.domain.finance.expense_month.schema import (
    ExpenseMonthSchema,
    PayloadExpenseMonthPersistSchema,
)

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
        expense: Expense,
        reference_year: int,
        payload: list[PayloadExpenseMonthPersistSchema],
    ) -> list[ExpenseMonth]:
        months_provided = {item.reference_month for item in payload}
        all_months = set(range(1, 13))
        missing_months = all_months - months_provided

        # Create missing months with default values
        for month in missing_months:
            payload.append(
                PayloadExpenseMonthPersistSchema(
                    reference_month=month,
                    amount=0.0,
                    paid_at=None,
                    status=None,
                )
            )

        # Sort by month for consistency
        payload.sort(key=lambda x: x.reference_month)

        expense_months = []
        for item in payload:
            expense_month = await self.persist(
                expense=expense,
                payload=item,
                with_throw=False,
                reference_year=reference_year,
            )
            expense_months.append(expense_month)
        return expense_months

    async def persist(
        self,
        expense: Expense,
        payload: PayloadExpenseMonthPersistSchema,
        reference_year: int,
        with_throw: bool = True,
    ) -> ExpenseMonth:
        status = get_status(
            status=payload.status,
            paid_at=payload.paid_at,
            reference_month=payload.reference_month,
        )
        paid_at = validate_paid_at(status, payload.paid_at)

        current_reference_year = payload.reference_year or reference_year

        expense_month = await self.find_by(
            expense_id=expense.id,
            reference_year=current_reference_year,
            reference_month=payload.reference_month,
            without_throw=True,
        )
        if expense_month:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail="Expense Month already exists",
                )
            else:
                expense.status = status
                expense.amount = payload.amount
                expense.paid_at = paid_at
                return await self.repository.update(entity=expense_month)

        else:
            return await self.repository.save(
                entity=ExpenseMonth(
                    status=status,
                    amount=payload.amount,
                    paid_at=paid_at,
                    expense_id=expense.id,
                    reference_year=current_reference_year,
                    reference_month=payload.reference_month,
                )
            )
