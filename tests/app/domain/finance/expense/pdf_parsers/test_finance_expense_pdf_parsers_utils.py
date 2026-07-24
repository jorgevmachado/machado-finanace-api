from decimal import Decimal
from datetime import date

from app.domain.finance.expense.pdf_parsers.utils import (
    get_date,
    get_number,
    get_number_money,
    parse_amount,
    get_date_with_named_month,
    get_date_with_named_month_without_year,
)


def test_get_date_returns_date() -> None:
    assert get_date("Vencimento: 15/07/2026") == date(2026, 7, 15)

def test_get_date_returns_none()  -> None:
    assert get_date("Vencimento: 15/07") is None


def test_get_number_and_get_number_money() -> None:
    assert get_number("Total da fatura anterior 3.650,94") == Decimal("3650.94")
    assert get_number_money("R$ 4.022,54 15/07/2026") == Decimal("4022.54")


def test_get_number_defaults_to_zero() -> None:
    assert get_number("sem numero") == Decimal("0")
    assert get_number_money("sem dinheiro") == Decimal("0")


def test_parse_amount() -> None:
    assert parse_amount("-3.650,94") == -3650.94

def test_get_date_with_named_month_successfully() -> None:
    result = get_date_with_named_month("Vencimento: 15 JUL 2026")
    assert result == date(2026, 7, 15)

def test_get_date_with_named_month_none() -> None:
    result = get_date_with_named_month("Vencimento: 15 2026")
    assert result is None
    
def test_get_date_with_named_month_without_year_successfully()  -> None: 
    result = get_date_with_named_month_without_year("15 JUL", 2026)
    assert result == date(2026, 7, 15)

def test_get_date_with_named_month_without_year_none()  -> None:
    result = get_date_with_named_month_without_year("15 2026", 2026)
    assert result is None