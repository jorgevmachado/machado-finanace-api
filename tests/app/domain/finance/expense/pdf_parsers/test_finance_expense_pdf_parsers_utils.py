from decimal import Decimal
from datetime import date

from app.domain.finance.expense.pdf_parsers.utils import (
    get_date,
    get_number,
    get_number_money,
    parse_amount,
)


def test_get_date_returns_date() -> None:
    assert get_date("Vencimento: 15/07/2026") == date(2026, 7, 15)


def test_get_number_and_get_number_money() -> None:
    assert get_number("Total da fatura anterior 3.650,94") == Decimal("3650.94")
    assert get_number_money("R$ 4.022,54 15/07/2026") == Decimal("4022.54")


def test_get_number_defaults_to_zero() -> None:
    assert get_number("sem numero") == Decimal("0")
    assert get_number_money("sem dinheiro") == Decimal("0")


def test_parse_amount() -> None:
    assert parse_amount("-3.650,94") == -3650.94
