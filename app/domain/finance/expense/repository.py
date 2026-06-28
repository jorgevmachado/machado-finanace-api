from __future__ import annotations

from app.core.repository.base import BaseRepository
from app.models import (
    Expense,
)

class ExpenseRepository(BaseRepository[Expense]):
    model = Expense
