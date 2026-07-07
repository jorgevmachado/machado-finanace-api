from __future__ import annotations

from typing import Annotated, cast, Optional

from fastapi import Query

from app.core.pagination import CustomLimitOffsetPage
from app.core.repository.base import BaseRepository
from app.models import Account, Allocation, Expense, AllocationContribution

from app.shared.schemas import FilterPage


class AccountRepository(BaseRepository[Account]):
    model = Account

    @staticmethod
    def _filter_expenses(expenses: list[Expense], reference_year: int) -> list[Expense]:
        filtered_expenses = []
        for expense in expenses or []:
            expense.months = [
                month
                for month in expense.months or []
                if month.reference_year == reference_year
                and month.deleted_at is None
            ]
            if expense.months:
                filtered_expenses.append(expense)
        return filtered_expenses
    
    @staticmethod
    def _filter_allocation_contributions(
        allocation_contributions: list[AllocationContribution],
         reference_year: int
    ) -> list[AllocationContribution]:

        filtered_allocation_contributions = []
        for allocation_contribution in allocation_contributions or []:
            allocation_contribution.months = [
                month
                for month in allocation_contribution.months or []
                if month.reference_year == reference_year and month.deleted_at is None
            ]
            if allocation_contribution.months:
                filtered_allocation_contributions.append(allocation_contribution)
        return filtered_allocation_contributions


    def _filter_allocation(
        self,
        allocation: Allocation,
       reference_year: int
    ) -> Allocation | None:
        allocation.expenses = self._filter_expenses(allocation.expenses, reference_year)
        allocation.allocation_contributions = self._filter_allocation_contributions(
            allocation.allocation_contributions,
            reference_year
        )
        if allocation.expenses or allocation.allocation_contributions:
            return allocation
        return None

    def _filter_allocations(
        self, allocations: list[Allocation], reference_year: int
    ) -> list[Allocation]:
        filtered_allocations = []
        for allocation in allocations or []:            
            allocation = self._filter_allocation(allocation, reference_year)
            if allocation:
                filtered_allocations.append(allocation)
        return filtered_allocations

    def _filter_account(self, account: Account, reference_year: int) -> Account:
        filtered_incomes = []
        for income in account.incomes or []:
            income.months = [
                month
                for month in income.months or []
                if month.reference_year == reference_year
                and month.deleted_at is None
            ]
            if income.months:
                filtered_incomes.append(income)
        account.incomes = filtered_incomes
        account.allocations = self._filter_allocations(
            allocations=account.allocations,
            reference_year=reference_year
        )
        return account

    def _filter_accounts(
        self, accounts: list[Account], reference_year: int
    ) -> list[Account]:
        filtered_accounts = [
            self._filter_account(account, reference_year)
            for account in accounts or []
            if account.deleted_at  is None
        ]
        return filtered_accounts

    async def list_all(self, page_filter: Annotated[FilterPage, Query()] = None):
        reference_year = cast(
            Optional[int], getattr(page_filter, "reference_year", None)
        )

        result = await super().list_all(page_filter)

        if reference_year is not None and isinstance(result, list):
            result = self._filter_accounts(result, reference_year)
            return result

        if reference_year is not None and  isinstance(result, CustomLimitOffsetPage):
            result.items = self._filter_accounts(result.items, reference_year)
            return result

        return result

    async def find_by(self, **kwargs) -> Account | None:
        reference_year = cast(
            Optional[int], kwargs.pop("reference_year", None)
        )

        result = await super().find_by(**kwargs)

        if result is not None and reference_year is not None:
            return  self._filter_account(cast(Account, result), reference_year)

        return result