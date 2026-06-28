from decimal import Decimal
from types import SimpleNamespace

from app.domain.finance.account.business import sum_amounts, sum_expenses_by_status
from app.models import ExpenseStatusEnum


def test_sum_amounts_returns_decimal_total() -> None:
    result = sum_amounts(
        [Decimal("10.50"), Decimal("2.25"), Decimal("0.25")]
    )

    assert result == Decimal("13.00")


def test_sum_transactions_by_status_filters_by_status() -> None:
    transactions = [
        SimpleNamespace(amount=Decimal("10.00"), status=ExpenseStatusEnum.PAID),
        SimpleNamespace(amount=Decimal("20.00"), status=ExpenseStatusEnum.PENDING),
        SimpleNamespace(amount=Decimal("30.00"), status=ExpenseStatusEnum.PAID),
    ]

    result = sum_expenses_by_status(
        transactions=transactions,
        status=ExpenseStatusEnum.PAID,
    )

    assert result == Decimal("40.00")
