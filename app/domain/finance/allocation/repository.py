from __future__ import annotations

from app.core.repository.base import BaseRepository
from app.models import (
    Allocation,
)


class AllocationRepository(BaseRepository[Allocation]):
    model = Allocation
