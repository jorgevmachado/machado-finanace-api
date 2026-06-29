from decimal import Decimal
from collections.abc import Iterable

from app.models import Expense, ExpenseStatusEnum

def sum_amounts(amounts: Iterable[Decimal]) -> Decimal:
    return sum(amounts, Decimal("0.00"))

def sum_expenses_by_status(
    expenses: list[Expense],
    status: ExpenseStatusEnum,
) -> Decimal:
    return sum_amounts(
        expense.amount
        for expense in expenses
        if expense.status == status
    )

