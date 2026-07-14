from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.account.business import DEFAULT_ACCOUNTS

from app.domain.finance.account.service import AccountService

from app.domain.finance.allocation.service import AllocationService
from app.domain.finance.allocation_contribution.service import (
    AllocationContributionService,
)
from app.domain.finance.category.business import DEFAULT_CATEGORIES
from app.domain.finance.category.service import CategoryService
from app.domain.finance.expense.service import ExpenseService
from app.domain.finance.income.service import IncomeService
from app.domain.finance.persist_schema import PayloadPersistSchema
from app.domain.finance.repository import FinanceRepository
from app.domain.finance.schema import (
    FinancePersistResultSchema,
    FinanceSchema,
)
from app.models import (
    Account,
    Finance,
    User,
    Expense,
    Category,
    Allocation,
    Income,
)

logger = logging.getLogger(__name__)


class FinanceService(BaseService[FinanceRepository, Finance]):
    def __init__(
        self,
        repository: FinanceRepository,
        account_service: AccountService | None = None,
        income_service: IncomeService | None = None,
        allocation_service: AllocationService | None = None,
        category_service: CategoryService | None = None,
        expense_service: ExpenseService | None = None,
        allocation_contribution_service: AllocationContributionService | None = None,
    ) -> None:
        super().__init__(
            alias="Finance",
            repository=repository,
            logger_params=LoggingParams(
                logger=logger, service="FinanceService", operation="finance"
            ),
            schema_class=FinanceSchema,
            cache_prefix="finance",
        )
        session = repository.session
        self.account_service = account_service or AccountService.from_session(session)
        self.income_service = income_service or IncomeService.from_session(session)
        self.allocation_service = allocation_service or AllocationService.from_session(
            session
        )
        self.category_service = category_service or CategoryService.from_session(
            session
        )
        self.expense_service = expense_service or ExpenseService.from_session(session)
        self.allocation_contribution_service = (
            allocation_contribution_service
            or AllocationContributionService.from_session(session)
        )

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(FinanceRepository(session))

    async def onboard(self, current_user: User) -> Finance:
        if current_user.finance:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"User {current_user.username} already onboarded",
            )
        finance = await self.repository.save(entity=Finance(user_id=current_user.id))
        for account in DEFAULT_ACCOUNTS:
            await self.account_service.persist(
                name=account.name,
                type=account.type,
                finance=finance,
                with_throw=False,
                initial_balance=account.initial_balance or 0,
            )
        for category in DEFAULT_CATEGORIES:
            await self.category_service.persist(
                name=category.name,
                finance=finance,
                description=category.description or category.name,
                with_throw=False,
            )

        return finance

    async def persist(
        self, finance: Finance, payloads: list[PayloadPersistSchema]
    ) -> FinancePersistResultSchema:
        incomes: list[Income] = []
        accounts: list[Account] = []
        expenses: list[Expense] = []
        categories: list[Category] = []
        allocations: list[Allocation] = []

        for payload in payloads:
            account = await self.account_service.persist(
                name=payload.name,
                type=payload.type,
                finance=finance,
                with_throw=False,
                initial_balance=payload.initial_balance or 0,
            )
            accounts.append(account)

            reference_day = payload.reference_day or 10
            reference_year = payload.reference_year

            incomes.extend(
                await self.income_service.persist_list(
                    account=account,
                    with_throw=False,
                    payloads=payload.incomes,
                    reference_day=reference_day,
                    reference_year=reference_year,
                )
            )

            for payload_allocation in payload.allocations:
                allocation = await self.allocation_service.persist(
                    name=payload_allocation.name,
                    account=account,
                    description=payload_allocation.description
                    or payload_allocation.name,
                    with_throw=False,
                )
                allocations.append(allocation)
                for payload_category in payload_allocation.categories:
                    category = await self.category_service.persist(
                        name=payload_category.name,
                        finance=finance,
                        description=payload_category.description
                        or payload_category.name,
                        with_throw=False,
                    )
                    categories.append(category)
                    for payload_expense in payload_category.expenses:
                        parent_expense = await self.expense_service.persist(
                            payee=payload_expense.name,
                            months=payload_expense.months or [],
                            category=category,
                            allocation=allocation,
                            with_throw=False,
                            description=payload_expense.description,
                            reference_day=reference_day,
                            reference_year=reference_year,
                        )
                        expenses.append(parent_expense)
                        payload_expense_children_categories = (
                            payload_expense.categories or []
                        )
                        if len(payload_expense_children_categories) > 0:
                            for (
                                payload_expense_children_category
                            ) in payload_expense_children_categories:
                                children_category = await self.category_service.persist(
                                    name=payload_expense_children_category.name,
                                    finance=finance,
                                    description=payload_expense_children_category.description
                                    or payload_expense_children_category.name,
                                    with_throw=False,
                                )
                                categories.append(children_category)
                                payload_children_expenses = (
                                    payload_expense_children_category.expenses or []
                                )
                                if len(payload_children_expenses) > 0:
                                    for (
                                        payload_children_expense
                                    ) in payload_children_expenses:
                                        child_expense = await self.expense_service.persist(
                                            payee=payload_children_expense.name,
                                            months=payload_children_expense.months
                                            or [],
                                            category=children_category,
                                            allocation=allocation,
                                            with_throw=False,
                                            description=payload_children_expense.description,
                                            reference_day=reference_day,
                                            reference_year=reference_year,
                                            parent_id=parent_expense.id,
                                        )
                                        expenses.append(child_expense)

        return FinancePersistResultSchema(
            incomes=len(incomes),
            accounts=len(accounts),
            expenses=len(expenses),
            categories=len(categories),
            allocations=len(allocations),
        )
