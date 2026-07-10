from __future__ import annotations

from typing import Annotated, cast, Optional

from fastapi import Query

from app.core.pagination import CustomLimitOffsetPage
from app.core.repository.base import BaseRepository
from app.models import (
    AllocationContribution,
    AllocationContributionMonth,
)
from app.shared.schemas import FilterPage


class AllocationContributionRepository(BaseRepository[AllocationContribution]):
    model = AllocationContribution

    @staticmethod
    def _filter_months(months: list[AllocationContributionMonth], reference_year: int) -> list[AllocationContributionMonth]:
        months = [
            month
            for month in months or []
            if month.reference_year == reference_year and month.deleted_at is None
        ]
        if months:
            return months
        return []

    def _filter_allocation_contributions(self, allocation_contributions: list[AllocationContribution], reference_year: int) -> list[AllocationContribution]:
        filtered_allocation_contributions = []
        for allocation_contribution in allocation_contributions or []:
            allocation_contribution.months = self._filter_months(allocation_contribution.months, reference_year)
            filtered_allocation_contributions.append(allocation_contribution)
        return filtered_allocation_contributions

    async def list_all(self, page_filter: Annotated[FilterPage, Query()] = None):
        reference_year = cast(
            Optional[int], getattr(page_filter, "reference_year", None)
        )

        result = await super().list_all(page_filter)

        if reference_year is not None and isinstance(result, list):
            result = self._filter_allocation_contributions(result, reference_year)
            return result

        if reference_year is not None and isinstance(result, CustomLimitOffsetPage):
            result.items = self._filter_allocation_contributions(result.items, reference_year)
            return result

        return result

    async def find_by(self, **kwargs) -> AllocationContribution | None:
        reference_year = cast(Optional[int], kwargs.pop("reference_year", None))
        result = await super().find_by(**kwargs)

        if reference_year is not None and result is not None:
            result.months = self._filter_months(cast(list[AllocationContributionMonth], result.months), reference_year)
            return result

        return result