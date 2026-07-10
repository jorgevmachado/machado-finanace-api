from __future__ import annotations

from typing import Annotated, Optional, cast

from sqlalchemy.orm import selectinload, Query

from app.core.pagination import CustomLimitOffsetPage
from app.core.repository.base import BaseRepository
from app.models import (
    Expense,
    ExpenseMonth,
)
from app.shared.schemas import FilterPage


class ExpenseRepository(BaseRepository[Expense]):
    model = Expense
    relations = (
        selectinload(Expense.children),
        selectinload(Expense.parent),
    )
    @staticmethod
    def _filter_months(months: list[ExpenseMonth], reference_year: int) -> list[ExpenseMonth]:
        months = [
            month
            for month in months or []
            if month.reference_year == reference_year and month.deleted_at is None
        ]
        if months:
            return months
        return []
    
    def _filter_expenses(self, expenses: list[Expense], reference_year: int) -> list[Expense]:
        filtered_expenses = []
        for expense in expenses or []:
            expense.months = self._filter_months(expense.months, reference_year)
            filtered_expenses.append(expense)
        return filtered_expenses

    async def list_all(self, page_filter: Annotated[FilterPage, Query()] = None):
        reference_year = cast(
            Optional[int], getattr(page_filter, "reference_year", None)
        )

        result = await super().list_all(page_filter)

        if reference_year is not None and isinstance(result, list):
            result = self._filter_expenses(result, reference_year)
            return result

        if reference_year is not None and isinstance(result, CustomLimitOffsetPage):
            result.items = self._filter_expenses(result.items, reference_year)
            return result

        return result

    async def find_by(self, **kwargs) -> Expense | None:
        reference_year = cast(
            Optional[int], kwargs.pop("reference_year", None)
        )
        result = await super().find_by(**kwargs)

        if reference_year is not None and result is not None:
            result.months = self._filter_months(cast(list[ExpenseMonth], result.months), reference_year)
            return result

        return result