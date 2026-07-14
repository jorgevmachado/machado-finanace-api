from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.domain.finance.allocation.schema import AllocationSchema
from app.domain.finance.expense import business
from app.domain.finance.expense.business import generate_months_by_year
from app.domain.finance.expense.pdf_parsers.schema import ParsedPDFSchema
from app.models import BankEnum, Category, utcnow, Allocation, Expense, ExpenseMonth, MonthStatusEnum


@pytest.fixture
def category():
    category = MagicMock(spec=Category)
    category.id = uuid4()
    category.finance_id = uuid4()
    category.name = "HEALTH"
    category.name_code = "health"
    category.finance_id = uuid4()
    category.description = "Category HEALTH generated from file upload"
    category.created_at = utcnow()
    category.updated_at = None
    category.deleted_at = None
    return category

@pytest.fixture
def allocation():
    allocation = MagicMock(spec=Allocation)
    allocation.id = uuid4()
    allocation.name = "Pessoal"
    allocation.name_code = "pessoal"
    allocation.is_active = True
    allocation.account_id = uuid4()
    allocation.description = "Alocação Pessoal"
    allocation.created_at = utcnow()
    allocation.updated_at = None
    allocation.deleted_at = None
    return allocation

@pytest.fixture
def expense_children(category, allocation):
    expense_1 = MagicMock(spec=Expense)
    expense_1.id = uuid4()
    expense_1.payee = "Test Payee"
    expense_1.months = []
    expense_1.payee_code = "test_payee"
    expense_1.category_id = category.id
    expense_1.category = category
    expense_1.description = "Test Expense"
    expense_1.allocation_id = allocation.id
    expense_1.allocation = allocation

    expense_2 = MagicMock(spec=Expense)
    expense_2.id = uuid4()
    expense_2.payee = "Test Payee 2"
    expense_2.months = []
    expense_2.payee_code = "test_payee_2"
    expense_2.category_id = category.id
    expense_2.category = category
    expense_2.description = "Test Expense 2"
    expense_2.allocation_id = allocation.id
    expense_2.allocation = allocation

    expense_3 = MagicMock(spec=Expense)
    expense_3.id = uuid4()
    expense_3.payee = "Test Payee 3"
    expense_3.months = []
    expense_3.payee_code = "test_payee_3"
    expense_3.category_id = category.id
    expense_3.category = category
    expense_3.description = "Test Expense 3"
    expense_3.allocation_id = allocation.id
    expense_3.allocation = allocation

    current_datetime = utcnow()
    reference_year = current_datetime.year

    for i in range(1, 13):
        expense_1_month = MagicMock(spec=ExpenseMonth)
        expense_1_month.month = i
        expense_1_month.amount = 100.00
        expense_1_month.status = MonthStatusEnum.PAID if i <= current_datetime.month else MonthStatusEnum.PENDING
        expense_1_month.description = f"Test Expense 1 Month {i} {reference_year}"
        expense_1_month.expense_id = expense_1.id
        expense_1_month.expense = expense_1
        expense_1_month.reference_year = reference_year
        expense_1_month.reference_month = i
        expense_1.months.append(expense_1_month)

        expense_1_other_year = MagicMock(spec=ExpenseMonth)
        expense_1_other_year.month = i
        expense_1_other_year.amount = 400.00
        expense_1_other_year.status = MonthStatusEnum.PAID if i <= current_datetime.month else MonthStatusEnum.PENDING
        expense_1_other_year.description = f"Test Expense 1 Month {i} {reference_year + 1}"
        expense_1_other_year.expense_id = expense_1.id
        expense_1_other_year.expense = expense_1
        expense_1_other_year.reference_year = reference_year + 1
        expense_1_other_year.reference_month = i
        expense_1.months.append(expense_1_other_year)
        #
        expense_2_month = MagicMock(spec=ExpenseMonth)
        expense_2_month.month = i
        expense_2_month.amount = 200.00
        expense_2_month.status = MonthStatusEnum.PAID if i <= current_datetime.month else MonthStatusEnum.PENDING
        expense_2_month.description = f"Test Expense 2 Month {i} {reference_year}"
        expense_2_month.expense_id = expense_2.id
        expense_2_month.expense = expense_2
        expense_2_month.reference_year = reference_year
        expense_2_month.reference_month = i
        expense_2.months.append(expense_2_month)
        #
        expense_2_other_year = MagicMock(spec=ExpenseMonth)
        expense_2_other_year.month = i
        expense_2_other_year.amount = 500.00
        expense_2_other_year.status = MonthStatusEnum.PAID if i <= current_datetime.month else MonthStatusEnum.PENDING
        expense_2_other_year.description = f"Test Expense 2 Month {i} {reference_year + 1}"
        expense_2_other_year.expense_id = expense_2.id
        expense_2_other_year.expense = expense_2
        expense_2_other_year.reference_year = reference_year + 1
        expense_2_other_year.reference_month = i
        expense_2.months.append(expense_2_other_year)
        #
        expense_3_month = MagicMock(spec=ExpenseMonth)
        expense_3_month.month = i
        expense_3_month.amount = 300.00
        expense_3_month.status = MonthStatusEnum.PAID if i <= current_datetime.month else MonthStatusEnum.PENDING
        expense_3_month.description = f"Test Expense 3 Month {i} {reference_year}"
        expense_3_month.expense_id = expense_3.id
        expense_3_month.expense = expense_3
        expense_3_month.reference_year = reference_year
        expense_3_month.reference_month = i
        expense_3.months.append(expense_3_month)

        expense_3_other_year = MagicMock(spec=ExpenseMonth)
        expense_3_other_year.month = i
        expense_3_other_year.amount = 600.00
        expense_3_other_year.status = MonthStatusEnum.PAID if i <= current_datetime.month else MonthStatusEnum.PENDING
        expense_3_other_year.description = f"Test Expense 3 Month {i} {reference_year + 1}"
        expense_3_other_year.expense_id = expense_3.id
        expense_3_other_year.expense = expense_3
        expense_3_other_year.reference_year = reference_year + 1
        expense_3_other_year.reference_month = i
        expense_3.months.append(expense_3_other_year)

    return [expense_1, expense_2, expense_3]

def _allocation_schema() -> AllocationSchema:
    return AllocationSchema(
        id=uuid4(),
        name="Moradia",
        expenses=[],
        name_code="moradia",
        is_active=True,
        account_id=uuid4(),
        description="allocation",
        allocation_contributions=[],
        created_at=datetime(2026, 1, 1, 0, 0, 0),
        updated_at=None,
        deleted_at=None,
    )


def test_generate_lines_pdf_extracts_text(monkeypatch) -> None:
    class _Page:
        def __init__(self, text: str | None):
            self._text = text

        def extract_text(self):
            return self._text

    class _Pdf:
        pages = [_Page("linha 1"), _Page(None), _Page("linha 2")]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(business.pdfplumber, "open", lambda _: _Pdf())

    result = business.generate_lines_pdf(b"%PDF")

    assert result == ["linha 1", "linha 2"]


def test_parse_pdf_calls_itau_parser(monkeypatch) -> None:
    allocation_schema = _allocation_schema()
    expected = ParsedPDFSchema(
        year=2026,
        bank=BankEnum.ITAU,
        error=False,
        message="Create Successfully!",
        expenses=[],
        allocation=allocation_schema,
        bill_total=0.0,
        bill_due_date=None,
        date_of_issue=None,
        reference_year=2026,
        reference_month=7,
        previous_bill_total=0.0,
        previous_bill_due_date=None,
    )

    monkeypatch.setattr(business, "generate_lines_pdf", lambda _: ["line a", "line b"])
    monkeypatch.setattr(
        business.AllocationSchema,
        "model_validate",
        lambda _: allocation_schema,
    )

    captured: dict = {}

    def _fake_parse_itau(lines, allocation, reference_year=None, reference_month=None):
        captured["lines"] = lines
        captured["allocation"] = allocation
        captured["reference_year"] = reference_year
        captured["reference_month"] = reference_month
        return expected

    monkeypatch.setattr(business, "parse_itau", _fake_parse_itau)

    result = business.parse_pdf(
        file=b"dummy",
        bank=BankEnum.ITAU,
        allocation=SimpleNamespace(),
        reference_year=2026,
        reference_month=7,
    )

    assert result == expected
    assert captured == {
        "lines": ["line a", "line b"],
        "allocation": allocation_schema,
        "reference_year": 2026,
        "reference_month": 7,
    }


def test_parse_pdf_returns_fallback_for_unimplemented_banks(monkeypatch) -> None:
    allocation_schema = _allocation_schema()
    monkeypatch.setattr(business, "generate_lines_pdf", lambda _: ["line a"])
    monkeypatch.setattr(
        business.AllocationSchema,
        "model_validate",
        lambda _: allocation_schema,
    )

    expected_nubank = ParsedPDFSchema(
        bank=BankEnum.NUBANK,
        error=False,
        message="Create Successfully!",
        expenses=[],
        allocation=allocation_schema,
        bill_total=0.0,
        bill_due_date=None,
        date_of_issue=None,
        reference_year=2026,
        reference_month=7,
        previous_bill_total=0.0,
        previous_bill_due_date=None,
    )
    monkeypatch.setattr(business, "parse_nubank", lambda **_: expected_nubank)

    nubank = business.parse_pdf(
        file=b"dummy",
        bank=BankEnum.NUBANK,
        allocation=SimpleNamespace(),
        reference_year=2026,
        reference_month=7,
    )
    caixa = business.parse_pdf(
        file=b"dummy",
        bank=BankEnum.CAIXA,
        allocation=SimpleNamespace(),
        reference_year=2026,
        reference_month=7,
    )

    assert nubank == expected_nubank

    assert caixa.error is True
    assert caixa.message == f"Not implemented yet for bank: {BankEnum.CAIXA.value}"
    assert caixa.expenses == []
    assert caixa.allocation == allocation_schema
    assert caixa.reference_year == 2026
    assert caixa.reference_month == 7


class TestGenerateMonthsByYear:
    @staticmethod
    def test_generate_months_by_year(expense_children):
        reference_year = utcnow().year
        reference_next_year = reference_year + 1

        result = generate_months_by_year(expenses=expense_children)
        assert len(result[reference_year]) == 12
        assert len(result[reference_next_year]) == 12
        for i in range(1, 13):
            assert result[reference_year][i-1].amount == 600.00
            assert result[reference_year][i-1].status == MonthStatusEnum.PAID if i <= utcnow().month else MonthStatusEnum.PENDING

            assert result[reference_next_year][i-1].amount == 1500.00
            assert result[reference_next_year][i-1].status == MonthStatusEnum.PAID if i <= utcnow().month else MonthStatusEnum.PENDING
        
