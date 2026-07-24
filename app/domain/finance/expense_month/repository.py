from __future__ import annotations

from app.core.repository.base import BaseRepository
from app.models import (
    ExpenseMonth,
)


class ExpenseMonthRepository(BaseRepository[ExpenseMonth]):
    model = ExpenseMonth
