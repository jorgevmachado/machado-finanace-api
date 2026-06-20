from __future__ import annotations

from app.core.repository.base import BaseRepository
from app.models import (
    Finance,
)


class FinanceRepository(BaseRepository[Finance]):
    model = Finance
