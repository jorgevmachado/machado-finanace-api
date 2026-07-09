from __future__ import annotations

from typing import Annotated, cast, Optional

from fastapi import Query

from app.core.pagination import CustomLimitOffsetPage
from app.core.repository.base import BaseRepository
from app.models import Income, IncomeMonth
from app.shared.schemas import FilterPage


class IncomeRepository(BaseRepository[Income]):
    model = Income

    @staticmethod
    def _filter_months(months: list[IncomeMonth], reference_year: int) -> list[IncomeMonth]:
        months = [
            month
            for month in months or []
            if month.reference_year == reference_year and month.deleted_at is None
        ]
        if months:
            return months
        return []
        
    
    def _filter_incomes(self, incomes: list[Income], reference_year: int) -> list[Income]:
        filtered_incomes = []
        for income in incomes or []:
            income.months = self._filter_months(income.months, reference_year)
            filtered_incomes.append(income)
        return filtered_incomes

    async def list_all(self, page_filter: Annotated[FilterPage, Query()] = None):
        reference_year = cast(
            Optional[int], getattr(page_filter, "reference_year", None)
        )
                
        result = await super().list_all(page_filter)        
        
        if reference_year is not None and isinstance(result, list):
            result = self._filter_incomes(result, reference_year)
            return result

        if reference_year is not None and  isinstance(result, CustomLimitOffsetPage):
            result.items = self._filter_incomes(result.items, reference_year)
            return result

        return result

    async def find_by(self, **kwargs) -> Income | None:
        reference_year = cast(
            Optional[int], kwargs.pop("reference_year", None)
        )
        result = await super().find_by(**kwargs)

        if reference_year is not None and result is not None:
            result.months = self._filter_months(cast(list[IncomeMonth], result.months), reference_year)
            return result

        return result