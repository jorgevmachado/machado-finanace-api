from __future__ import annotations

import logging
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService

from app.domain.finance.allocation.service import AllocationService

from app.domain.finance.category.service import CategoryService

from app.domain.finance.expense.repository import (
    ExpenseRepository,
)
from app.domain.finance.expense.schema import (
    ExpenseSchema,
    PayloadExpenseCreateSchema,
)
from app.domain.finance.expense_month.service import ExpenseMonthService
from app.domain.finance.months.schema import PayloadMonthPersistSchema

from app.models import (
    Expense,
    Finance,
    Allocation,
    Category,
)
from app.shared.utils.string import to_snake_case
from app.shared.utils.validator import validate_year

logger = logging.getLogger(__name__)


class ExpenseService(BaseService[ExpenseRepository, Expense]):
    def __init__(
        self,
        repository: ExpenseRepository,
        category_service: CategoryService | None = None,
        allocation_service: AllocationService | None = None,
        expense_month_service: ExpenseMonthService | None = None,
    ) -> None:
        super().__init__(
            alias="Expense",
            repository=repository,
            logger_params=LoggingParams(
                logger=logger,
                service="ExpenseService",
                operation="expense",
            ),
            schema_class=ExpenseSchema,
            cache_prefix="expense",
        )
        session = repository.session
        self.category_service = category_service or CategoryService.from_session(
            session
        )
        self.allocation_service = allocation_service or AllocationService.from_session(
            session
        )
        self.expense_month_service = (
            expense_month_service or ExpenseMonthService.from_session(session)
        )

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(ExpenseRepository(session))

    async def create(
        self, finance: Finance, payload: PayloadExpenseCreateSchema
    ) -> Expense:

        allocation = await self.allocation_service.find_by(
            id=payload.allocation_id, without_throw=True
        )
        if not allocation:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Allocation with this id {payload.allocation_id} does not exist",
            )

        category = await self.category_service.find_by(
            id=payload.category_id,
            finance_id=finance.id,
            without_throw=True,
        )

        if not category:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Category {payload.category_id} not found for finance {finance.id}",
            )

        return await self.persist(
            payee=payload.payee,
            months=payload.months,
            category=category,
            allocation=allocation,
            with_throw=True,
            description=payload.description,
            reference_day=payload.reference_day or 10,
            reference_year=payload.reference_year,
        )

    async def persist(
        self,
        payee: str,
        months: list[PayloadMonthPersistSchema],
        category: Category,
        allocation: Allocation,
        description: str,
        reference_day: int,
        reference_year: int,
        parent_id: UUID | None = None,
        with_throw: bool = True,
    ) -> Expense:

        year = validate_year(reference_year)

        payee_code = to_snake_case(payee)

        expense = await self.find_by(
            payee_code=payee_code,
            category_id=category.id,
            description=description,
            allocation_id=allocation.id,
            without_throw=True,
        )
        if expense:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Expense with payee {payee} already exists",
                )
            else:
                expense.description = description
                expense.parent_id = parent_id
                updated_months = await self.expense_month_service.persist_list(
                    months=months,
                    expense=expense,
                    reference_year=year,
                    reference_day=reference_day,
                )
                updated_expense = await self.repository.update(entity=expense)
                updated_expense.months = updated_months
                return updated_expense

        else:
            created_expense = await self.repository.save(
                entity=Expense(
                    payee=payee,
                    parent_id=parent_id,
                    payee_code=payee_code,
                    category_id=category.id,
                    description=description,
                    allocation_id=allocation.id,
                )
            )
            saved_months = await self.expense_month_service.persist_list(
                months=months,
                expense=created_expense,
                reference_day=reference_day,
                reference_year=year,
            )

            saved_expense = await self.find_by(id=created_expense.id)
            saved_expense.months = saved_months
            return saved_expense
