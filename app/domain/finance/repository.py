from __future__ import annotations

from sqlalchemy.orm import selectinload

from app.core.repository.base import BaseRepository
from app.models import Finance, Allocation, Expense, Account


class FinanceRepository(BaseRepository[Finance]):
    model = Finance
    relations = (
        selectinload(Finance.accounts).selectinload(Account.allocations).selectinload(Allocation.expenses).selectinload(Expense.children),
    )
