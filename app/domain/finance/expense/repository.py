from __future__ import annotations

from sqlalchemy.orm import joinedload, selectinload

from app.core.repository.base import BaseRepository
from app.models import (
    Expense,
)


class ExpenseRepository(BaseRepository[Expense]):
    model = Expense

    def __init__(self, session):
        super().__init__(session)
        self.relations = [
            joinedload(Expense.parent),
            selectinload(Expense.children),
        ]
