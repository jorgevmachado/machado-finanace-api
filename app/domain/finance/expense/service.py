from __future__ import annotations

import logging
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.account.service import AccountService

from app.domain.finance.allocation.service import AllocationService
from app.domain.finance.category.schema import PayloadCategoryCreateSchema
from app.domain.finance.category.service import CategoryService

from app.domain.finance.expense.repository import (
    ExpenseRepository,
)
from app.domain.finance.expense.schema import (
    ExpenseSchema,
    PayloadExpenseCreateSchema,
)
from app.domain.finance.expense_month.service import ExpenseMonthService
from app.domain.finance.schema import FinanceCreateCategorySchema

from app.models import (
    Expense,
    Finance,
    Account,
    Allocation,
    Category,
)

logger = logging.getLogger(__name__)


class ExpenseService(BaseService[ExpenseRepository, Expense]):
    def __init__(
        self,
        repository: ExpenseRepository,
        account_service: AccountService | None = None,
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
        self.account_service = account_service or AccountService.from_session(session)
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

        account, allocation = await self._validate_relations(
            finance=finance,
            account_id=payload.account_id,
            allocation_id=payload.allocation_id,
        )

        category = await self._validate_category(payload.category_id, finance.id)

        return await self.persist(
            finance=finance,
            account=account,
            allocation=allocation,
            category=category,
            payload=payload,
            with_throw=True,
        )

    async def _validate_relations(
        self,
        finance: Finance,
        account_id: UUID,
        allocation_id: UUID,
    ):
        account = await self.account_service.find_by(
            id=account_id, finance_id=finance.id, without_throw=True
        )
        if not account:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Account with this id {account_id} does not exist",
            )

        allocation = await self.allocation_service.find_by(
            id=allocation_id, without_throw=True
        )
        if not allocation:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Allocation with this id {allocation_id} does not exist",
            )

        return account, allocation

    async def _validate_category(self, category_id: UUID, finance_id: UUID) -> Category:
        category = await self.category_service.find_by(
            id=category_id, finance_id=finance_id, without_throw=True
        )
        if not category:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Category {category_id} not found for finance {finance_id}",
            )
        return category

    async def persist(
        self,
        finance: Finance,
        account: Account,
        category: Category,
        allocation: Allocation,
        payload: PayloadExpenseCreateSchema,
        with_throw: bool = True,
    ) -> Expense:

        expense = await self.find_by(
            finance_id=finance.id,
            account_id=account.id,
            allocation_id=allocation.id,
            category_id=category.id,
            description=payload.description,
            without_throw=True,
        )
        if expense:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail="Expense already exists",
                )
            else:
                expense.description = payload.description
                await self.expense_month_service.persist_list(
                    expense=expense,
                    reference_year=payload.reference_year,
                    payload=payload.months,
                )
                return await self.repository.update(entity=expense)

        else:
            created_expense = await self.repository.save(
                entity=Expense(
                    finance_id=finance.id,
                    account_id=payload.account_id,
                    category_id=payload.category_id,
                    description=payload.description,
                    allocation_id=payload.allocation_id,
                )
            )
            await self.expense_month_service.persist_list(
                expense=created_expense,
                reference_year=payload.reference_year,
                payload=payload.months,
            )

            return await self.find_by(id=created_expense.id)

    async def create_by_account(
        self,
        finance: Finance,
        account: Account,
        allocation: Allocation,
        reference_day: int,
        reference_year: int,
        payload_categories: list[FinanceCreateCategorySchema],
    ) -> list[Expense]:
        expenses: list[Expense] = []
        if len(payload_categories) > 0:
            for payload_category in payload_categories:
                category = await self.category_service.persist(
                    finance=finance,
                    payload=PayloadCategoryCreateSchema(
                        name=payload_category.name,
                        type=payload_category.type,
                        description=payload_category.description
                        or payload_category.name,
                    ),
                    with_throw=False,
                )
                payload_months = payload_category.months or []

                expense = await self.persist(
                    finance=finance,
                    account=account,
                    category=category,
                    allocation=allocation,
                    payload=PayloadExpenseCreateSchema(
                        months=payload_months,
                        account_id=account.id,
                        description=payload_category.description
                        or payload_category.name,
                        category_id=category.id,
                        allocation_id=allocation.id,
                        reference_day=reference_day,
                        reference_year=reference_year,
                    ),
                    with_throw=False,
                )
                expenses.append(expense)
        return expenses
