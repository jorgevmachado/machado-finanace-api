from __future__ import annotations

from typing import Annotated, cast, Optional

from fastapi import Query

from app.core.pagination import CustomLimitOffsetPage
from app.core.repository.base import BaseRepository
from app.models import Account, Allocation

from app.shared.schemas import FilterPage


class AccountRepository(BaseRepository[Account]):
    model = Account

    @staticmethod
    def _filter_allocations(
        allocations: list[Allocation], reference_year: int
    ) -> list[Allocation]:
        for allocation in allocations or []:
            for expense in allocation.expenses or []:
                expense.months = [
                    month
                    for month in expense.months or []
                    if month.reference_year == reference_year
                    and month.deleted_at is None
                ]
            for allocation_contribution in allocation.allocation_contributions or []:
                allocation_contribution.months = [
                    month
                    for month in allocation_contribution.months or []
                    if month.reference_year == reference_year
                    and month.deleted_at is None
                ]
        return allocations

    def _filter_months(
        self, accounts: list[Account], reference_year: int
    ) -> list[Account]:
        for account in accounts:
            for income in account.incomes or []:
                income.months = [
                    month
                    for month in income.months or []
                    if month.reference_year == reference_year
                    and month.deleted_at is None
                ]
            account.allocations = self._filter_allocations(
                allocations=account.allocations, reference_year=reference_year
            )
        return accounts

    async def list_all(self, page_filter: Annotated[FilterPage, Query()] = None):
        reference_year = cast(
            Optional[int], getattr(page_filter, "reference_year", None)
        )

        result = await super().list_all(page_filter)

        if reference_year is not None and isinstance(result, list):
            result = self._filter_months(result, reference_year)
            return result

        if reference_year is not None and  isinstance(result, CustomLimitOffsetPage):
            print("# => list_all => paginate => ")
            result.items = self._filter_months(result.items, reference_year)
            return result

        return result
