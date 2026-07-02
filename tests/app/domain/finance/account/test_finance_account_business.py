from decimal import Decimal
from types import SimpleNamespace

from app.domain.finance.account.business import sum_amounts, sum_expenses_by_status
from app.models import MonthStatusEnum


def test_sum_amounts_returns_decimal_total() -> None:
    result = sum_amounts([Decimal("10.50"), Decimal("2.25"), Decimal("0.25")])
    assert result == Decimal("13.00")


def test_sum_amounts_empty_list() -> None:
    result = sum_amounts([])
    assert result == Decimal("0.00")


def test_sum_expenses_by_status_filters_by_paid() -> None:
    expenses = [
        SimpleNamespace(
            months=[
                SimpleNamespace(amount=Decimal("10.00"), status=MonthStatusEnum.PAID),
                SimpleNamespace(
                    amount=Decimal("5.00"), status=MonthStatusEnum.PENDING
                ),
            ]
        ),
        SimpleNamespace(
            months=[
                SimpleNamespace(
                    amount=Decimal("20.00"), status=MonthStatusEnum.PENDING
                ),
                SimpleNamespace(amount=Decimal("15.00"), status=MonthStatusEnum.PAID),
            ]
        ),
    ]

    result = sum_expenses_by_status(
        [{"months": [m.__dict__ for m in exp.months]} for exp in expenses],
        MonthStatusEnum.PAID,
    )

    assert result == Decimal("25.00")


def test_sum_expenses_by_status_filters_by_pending() -> None:
    expenses = [
        SimpleNamespace(
            months=[
                SimpleNamespace(amount=Decimal("10.00"), status=MonthStatusEnum.PAID),
                SimpleNamespace(
                    amount=Decimal("5.00"), status=MonthStatusEnum.PENDING
                ),
            ]
        ),
        SimpleNamespace(
            months=[
                SimpleNamespace(
                    amount=Decimal("20.00"), status=MonthStatusEnum.PENDING
                ),
                SimpleNamespace(amount=Decimal("15.00"), status=MonthStatusEnum.PAID),
            ]
        ),
    ]

    result = sum_expenses_by_status(
        [{"months": [m.__dict__ for m in exp.months]} for exp in expenses],
        MonthStatusEnum.PENDING,
    )

    assert result == Decimal("25.00")


def test_sum_expenses_by_status_no_months() -> None:
    expenses = [{"months": []}]
    result = sum_expenses_by_status(expenses, MonthStatusEnum.PAID)
    assert result == Decimal("0.00")


def test_sum_expenses_by_status_empty_expenses() -> None:
    result = sum_expenses_by_status([], MonthStatusEnum.PAID)
    assert result == Decimal("0.00")
