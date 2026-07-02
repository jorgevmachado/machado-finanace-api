from __future__ import annotations

from app.core.repository.base import BaseRepository
from app.models import (
    AllocationContributionMonth,
)


class AllocationContributionMonthRepository(
    BaseRepository[AllocationContributionMonth]
):
    model = AllocationContributionMonth
