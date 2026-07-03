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
from app.domain.finance.expense.business import get_expense_months, get_expense_children
from app.domain.finance.category.schema import PayloadCategoryCreateSchema
from app.domain.finance.category.service import CategoryService

from app.domain.finance.expense.repository import (
    ExpenseRepository,
)
from app.domain.finance.expense.schema import (
    ExpenseSchema,
    PayloadExpenseCreateSchema,
    PayloadFinanceExpensePersistChildrenRequiredSchema,
)
from app.domain.finance.expense_month.service import ExpenseMonthService
from app.domain.finance.months.schema import PayloadMonthPersistSchema
from app.domain.finance.schema import PayloadFinanceCategoryPersistSchema

from app.models import (
    Expense,
    Finance,
    Account,
    Allocation,
    Category,
)
from app.shared.utils.validator import validate_year

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
            months=payload.months,
            account=account,
            finance=finance,
            category=category,
            allocation=allocation,
            with_throw=True,
            description=payload.description,
            reference_day=payload.reference_day or 10,
            reference_year=payload.reference_year,
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

    async def persist_by_category(
        self,
        finance: Finance,
        account: Account,
        payload: PayloadFinanceCategoryPersistSchema,
        allocation: Allocation,
        reference_day: int,
        reference_year: int,
    ) -> list[Expense]:
        expenses: list[Expense] = []
        category = await self.category_service.persist(
            finance=finance,
            payload=payload,
            with_throw=False,
        )
        merged_expenses_months = get_expense_months(
            payloads=payload.expenses or [], category_type=payload.type
        )

        if len(merged_expenses_months) > 0:
            expense = await self.persist(
                months=merged_expenses_months,
                account=account,
                finance=finance,
                category=category,
                allocation=allocation,
                description=category.description,
                reference_day=reference_day,
                reference_year=reference_year,
                with_throw=False,
            )
            expenses.append(expense)

            payload_expenses = get_expense_children(
                payloads=payload.expenses or [], category_type=payload.type
            )

            if len(payload_expenses) > 0:
                for payload_expense in payload_expenses:
                    children_expenses = await self.persist_children(
                        parent=expense,
                        children=payload_expense.children,
                        reference_day=reference_day,
                        reference_year=reference_year,
                        reference_month=payload_expense.reference_month,
                    )
                    expenses.extend(children_expenses)

        return expenses

    async def persist_children(
        self,
        parent: Expense,
        children: list[PayloadFinanceExpensePersistChildrenRequiredSchema],
        reference_day: int,
        reference_year: int,
        reference_month: int,
    ) -> list[Expense]:
        expenses: list[Expense] = []
        for payload_category in children:
            category = await self.category_service.persist(
                finance=parent.finance,
                payload=PayloadCategoryCreateSchema(
                    name=payload_category.name,
                    type=payload_category.type,
                    description=payload_category.description or payload_category.name,
                ),
                with_throw=False,
            )
            expense = await self.persist(
                months=[
                    PayloadMonthPersistSchema(
                        amount=payload_category.amount,
                        reference_month=reference_month,
                    )
                ],
                account=parent.account,
                finance=parent.finance,
                category=category,
                parent_id=parent.id,
                allocation=parent.allocation,
                description=category.description,
                reference_day=reference_day,
                reference_year=reference_year,
                with_throw=False,
            )
            expenses.append(expense)
        return expenses

    async def persist(
        self,
        months: list[PayloadMonthPersistSchema],
        account: Account,
        finance: Finance,
        category: Category,
        allocation: Allocation,
        description: str,
        reference_day: int,
        reference_year: int,
        parent_id: UUID | None = None,
        with_throw: bool = True,
    ) -> Expense:

        year = validate_year(reference_year)

        expense = await self.find_by(
            finance_id=finance.id,
            account_id=account.id,
            allocation_id=allocation.id,
            category_id=category.id,
            description=description,
            without_throw=True,
        )
        if expense:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail="Expense already exists",
                )
            else:
                expense.description = description
                expense.parent_id = parent_id
                await self.expense_month_service.persist_list(
                    months=months,
                    expense=expense,
                    reference_year=year,
                    reference_day=reference_day,
                )
                return await self.repository.update(entity=expense)

        else:
            created_expense = await self.repository.save(
                entity=Expense(
                    parent_id=parent_id,
                    finance_id=finance.id,
                    account_id=account.id,
                    category_id=category.id,
                    description=description,
                    allocation_id=allocation.id,
                )
            )
            await self.expense_month_service.persist_list(
                months=months,
                expense=created_expense,
                reference_day=reference_day,
                reference_year=year,
            )

            return await self.find_by(id=created_expense.id)
