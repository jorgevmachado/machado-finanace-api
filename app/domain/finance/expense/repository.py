from __future__ import annotations

from sqlalchemy.orm import selectinload

from app.core.repository.base import BaseRepository
from app.models import (
    Expense,
)


class ExpenseRepository(BaseRepository[Expense]):
    model = Expense
    relations = (
        selectinload(Expense.children),
        selectinload(Expense.parent),
    )
