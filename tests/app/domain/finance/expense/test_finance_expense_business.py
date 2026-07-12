from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

from app.domain.finance.allocation.schema import AllocationSchema
from app.domain.finance.expense import business
from app.domain.finance.expense.pdf_parsers.schema import ParsedPDFSchema
from app.models import BankEnum


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
