from __future__ import annotations

from app.core.repository.base import BaseRepository
from app.models import (
    AllocationContribution,
)


class AllocationContributionRepository(BaseRepository[AllocationContribution]):
    model = AllocationContribution
