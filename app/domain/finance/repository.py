from __future__ import annotations

from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import with_loader_criteria

from app.core.repository.base import BaseRepository
from app.models import (
    Account,
    Allocation,
    AllocationContribution,
    Expense,
    Finance,
    Income,
)


class FinanceRepository(BaseRepository[Finance]):
    model = Finance

    async def find_by_finance_year(
        self,
        finance_id: UUID,
        reference_year: int,
        with_deleted: bool = False,
    ) -> Finance | None:
        income_year_predicate = Income.reference_year == reference_year
        contribution_year_predicate = (
            AllocationContribution.reference_year == reference_year
        )
        expense_year_predicate = (
            func.extract(
                "year",
                func.coalesce(Expense.paid_at, Expense.created_at),
            )
            == reference_year
        )

        if not with_deleted:
            income_year_predicate = and_(
                Income.deleted_at.is_(None),
                income_year_predicate,
            )
            contribution_year_predicate = and_(
                AllocationContribution.deleted_at.is_(None),
                contribution_year_predicate,
            )
            expense_year_predicate = and_(
                Expense.deleted_at.is_(None),
                expense_year_predicate,
            )

        account_year_predicate = or_(
            Account.incomes.any(income_year_predicate),
            Account.expenses.any(expense_year_predicate),
            Account.allocation_contributions.any(contribution_year_predicate),
        )
        allocation_year_predicate = or_(
            Allocation.expenses.any(expense_year_predicate),
            Allocation.allocation_contributions.any(contribution_year_predicate),
        )

        if not with_deleted:
            account_year_predicate = and_(
                Account.deleted_at.is_(None),
                account_year_predicate,
            )
            allocation_year_predicate = and_(
                Allocation.deleted_at.is_(None),
                allocation_year_predicate,
            )

        income_count = await self.session.scalar(
            select(func.count())
            .select_from(Income)
            .where(Income.finance_id == finance_id, income_year_predicate)
        )
        expense_count = await self.session.scalar(
            select(func.count())
            .select_from(Expense)
            .where(Expense.finance_id == finance_id, expense_year_predicate)
        )
        contribution_count = await self.session.scalar(
            select(func.count())
            .select_from(AllocationContribution)
            .where(
                AllocationContribution.finance_id == finance_id,
                contribution_year_predicate,
            )
        )

        yearly_total = (
            int(income_count or 0)
            + int(expense_count or 0)
            + int(contribution_count or 0)
        )
        if yearly_total == 0:
            return None

        query = (
            select(Finance)
            .where(Finance.id == finance_id)
            .execution_options(populate_existing=True)
            .options(
                with_loader_criteria(
                    Income, income_year_predicate, include_aliases=True
                ),
                with_loader_criteria(
                    Expense, expense_year_predicate, include_aliases=True
                ),
                with_loader_criteria(
                    AllocationContribution,
                    contribution_year_predicate,
                    include_aliases=True,
                ),
                with_loader_criteria(
                    Account, account_year_predicate, include_aliases=True
                ),
                with_loader_criteria(
                    Allocation, allocation_year_predicate, include_aliases=True
                ),
            )
        )

        if not with_deleted:
            query = query.where(Finance.deleted_at.is_(None))

        return await self.session.scalar(query)
