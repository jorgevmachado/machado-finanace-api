from decimal import Decimal
from collections.abc import Iterable


def sum_amounts(amounts: Iterable[Decimal]) -> Decimal:
    return sum(amounts, Decimal("0.00"))

def sum_expenses_by_status(expenses: list, status: str) -> Decimal:
    return sum_amounts(
        month["amount"]
        for obj in expenses
        for month in obj.get("months", [])
        if month.get("status") == status
    )
