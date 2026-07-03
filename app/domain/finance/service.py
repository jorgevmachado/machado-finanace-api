from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Annotated

from fastapi import HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.account.schema import PayloadAccountCreateSchema
from app.domain.finance.account.service import AccountService
from app.domain.finance.allocation.schema import (
    PayloadAllocationCreateSchema,
)
from app.domain.finance.allocation.service import AllocationService
from app.domain.finance.allocation_contribution.service import (
    AllocationContributionService,
)
from app.domain.finance.business import has_yearly_data

from app.domain.finance.category.service import CategoryService
from app.domain.finance.expense.service import ExpenseService
from app.domain.finance.income.service import IncomeService
from app.domain.finance.repository import FinanceRepository
from app.domain.finance.schema import (
    FinancePersistResultSchema,
    FinanceSchema,
    PayloadFinancePersistSchema,
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
from app.shared.schemas import FilterPage
from app.shared.utils.validator import validate_year

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
        return await self.repository.save(entity=Finance(user_id=current_user.id))

    async def find_by_user(
        self,
        current_user: User,
        page_filter: Annotated[FilterPage, Query()] = None,
    ) -> Finance:
        finance = current_user.finance if current_user.finance else None
        if not finance:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"User {current_user.username} must be onboarded first",
            )
        year = getattr(page_filter, "year", None) if page_filter else None
        with_deleted = page_filter.with_deleted if page_filter else False
        if year is not None:
            reference_year = validate_year(year)
            result = await self.repository.find_by_finance_year(
                finance_id=finance.id,
                reference_year=reference_year,
                with_deleted=with_deleted or False,
            )
            if result is None or not has_yearly_data(result):
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"{self.alias} not found",
                )
            return result

        return await self.find_one(param=str(finance.id))

    async def persist(
        self, finance: Finance, payloads: list[PayloadFinancePersistSchema]
    ) -> FinancePersistResultSchema:
        incomes: list[Income] = []
        accounts: list[Account] = []
        expenses: list[Expense] = []
        categories: list[Category] = []
        allocations: list[Allocation] = []

        for payload in payloads:
            account = await self.account_service.persist(
                finance=finance,
                payload=PayloadAccountCreateSchema(
                    name=payload.name,
                    type=payload.type,
                    initial_balance=payload.initial_balance or 0,
                ),
                with_throw=False,
            )
            accounts.append(account)
            reference_day = payload.reference_day or 10
            reference_year = payload.reference_year

            for payload_income in payload.incomes:
                income = await self.income_service.persist(
                    months=payload_income.months,
                    source=payload_income.source,
                    finance=finance,
                    account=account,
                    with_throw=False,
                    description=payload_income.description,
                    reference_day=reference_day,
                    reference_year=reference_year,
                )
                incomes.append(income)

            for payload_allocation in payload.allocations:
                allocation = await self.allocation_service.persist(
                    finance=finance,
                    payload=PayloadAllocationCreateSchema(
                        name=payload_allocation.name,
                        type=payload_allocation.type,
                        description=payload_allocation.description
                        or payload_allocation.name,
                    ),
                    with_throw=False,
                )
                allocations.append(allocation)

                for payload_category in payload_allocation.categories:
                    expenses_persisted: list[
                        Expense
                    ] = await self.expense_service.persist_by_category(
                        finance=finance,
                        account=account,
                        payload=payload_category,
                        allocation=allocation,
                        reference_day=reference_day,
                        reference_year=reference_year,
                    )
                    for expense_persisted in expenses_persisted:
                        if expense_persisted.category:
                            categories.append(expense_persisted.category)
                    expenses.extend(expenses_persisted)

        return FinancePersistResultSchema(
            incomes=len(incomes),
            accounts=len(accounts),
            expenses=len(expenses),
            categories=len(categories),
            allocations=len(allocations),
        )
