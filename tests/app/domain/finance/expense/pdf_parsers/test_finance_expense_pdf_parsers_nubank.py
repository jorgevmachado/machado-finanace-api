from datetime import datetime, date
from uuid import uuid4

from app.domain.finance.allocation.schema import AllocationSchema
from app.domain.finance.expense.pdf_parsers.nubank import (
    parse_expenses,
    parse_nubank,
    _extract_transaction_year,
    build_parsed_pdf_expenses,
)
from app.models import utcnow


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


def _nubank_lines() -> list[str]:
    return [
        "Data de vencimento: 13 JUL 2026",
        "fatura no valor de R$ 541,62",
        "FATURA 13 JUL 2026 EMISSÃO E ENVIO 04 JUL 2026",
        "Fatura anterior R$ 448,99",
        "Pagamentos -R$ 448,99",
        "10 JUN Pagamento em 10 JUN −R$ 448,99",
        "TRANSAÇÕES DE 04 JUN A 04 JUL",
        "Jorge L V S Filho R$ 541,62",
        "04 JUN •••• 0941 Dl*Google Google R$ 9,99",
        "11 JUN •••• 8072 Amazon R$ 72,18",
        "16 JUN •••• 8589 Pg *Cod3r Ensino e Con - Parcela 1/12 R$ 49,72",
        "17 JUN •••• 0221 Mp *Melimais R$ 19,90",
        "24 JUN •••• 0221 Mercadolivre*Mercadol R$ 94,93",
        "27 JUN •••• 6560 Ifd*Ifood Club R$ 12,90",
        "30 JUN •••• 0941 Drogaria Pacheco R$ 65,57",
        "02 JUL •••• 7052 Netflix Entretenimento R$ 44,90",
        "02 JUL •••• 7052 Dm*Helphbomaxcom R$ 22,45",
        "03 JUL •••• 8072 Amazonmktplc*Casaaladi - Parcela 1/2 R$ 149,08",
        "Pagamentos -R$ 448,99",
        "10 JUN Pagamento em 10 JUN −R$ 448,99"
    ]


def test_parse_expenses_extracts_nubank_transactions() -> None:
    result = parse_expenses(_nubank_lines())

    assert len(result) == 10
    assert result[0] == {
        "date": "2026-06-04",
        "payee": "Dl*Google Google",
        "total_of_installments": 1,
        "current_installment": 1,
        "amount": 9.99,
        "category": None,
        "reference_month": 6,
    }
    assert result[2] == {
        "date": "2026-06-16",
        "payee": "Pg *Cod3r Ensino e Con",
        "total_of_installments": 12,
        "current_installment": 1,
        "amount": 49.72,
        "category": None,
        "reference_month": 6,
    }
    assert result[-1] == {
        "date": "2026-07-03",
        "payee": "Amazonmktplc*Casaaladi",
        "total_of_installments": 2,
        "current_installment": 1,
        "amount": 149.08,
        "category": None,
        "reference_month": 7,
    }


def test_parse_nubank_builds_parsed_expense_schema() -> None:
    result = parse_nubank(lines=_nubank_lines(), allocation=_allocation_schema())

    assert result.error is False
    assert len(result.expenses) == 10
    assert result.expenses[0].date.isoformat() == "2026-06-04"
    assert result.expenses[0].payee == "Dl*Google Google"
    assert result.expenses[0].amount == 9.99
    assert result.expenses[0].category is None
    assert result.expenses[0].reference_month == 6
    assert result.expenses[0].current_installment == 1
    assert result.expenses[0].total_of_installments == 1

def test_parse_nubank_builds_parsed_expense_with_different_year() -> None:
    result = parse_nubank(lines=_nubank_lines(), allocation=_allocation_schema(), reference_year=2025)

    assert result.error is True
    assert result.message == "Reference year is different from document"

def test_parse_nubank_builds_parsed_expense_with_different_month() -> None:
    result = parse_nubank(lines=_nubank_lines(), allocation=_allocation_schema(), reference_month=1)

    assert result.error is True
    assert result.message == "Reference month is different from document"

def test_parse_nubank_builds_parsed_expense_when_expense_list_is_empty() -> None:
    lines = [
        "Data de vencimento: 13 JUL 2026",
        "fatura no valor de R$ 541,62",
        "FATURA 13 JUL 2026 EMISSÃO E ENVIO 04 JUL 2026",
        "Fatura anterior R$ 448,99",
        "Pagamentos -R$ 448,99",
        "10 JUN Pagamento em 10 JUN −R$ 448,99",
        "TRANSAÇÕES DE 04 JUN A 04 JUL",
        "Jorge L V S Filho R$ 541,62",
        "Pagamentos -R$ 448,99",
        "10 JUN Pagamento em 10 JUN −R$ 448,99"
    ]
    result = parse_nubank(lines=lines, allocation=_allocation_schema())

    assert result.error is True
    assert result.message == "No expenses found in the document"

def test_extract_transaction_year_with_utcnow() -> None:
    lines = [
        "Data de vencimento: 13 JUL 2026",
        "fatura no valor de R$ 541,62",
        "Fatura anterior R$ 448,99",
        "Pagamentos -R$ 448,99",
        "10 JUN Pagamento em 10 JUN −R$ 448,99",
        "TRANSAÇÕES DE 04 JUN A 04 JUL",
        "Jorge L V S Filho R$ 541,62",
        "04 JUN •••• 0941 Dl*Google Google R$ 9,99",
        "11 JUN •••• 8072 Amazon R$ 72,18",
        "16 JUN •••• 8589 Pg *Cod3r Ensino e Con - Parcela 1/12 R$ 49,72",
        "17 JUN •••• 0221 Mp *Melimais R$ 19,90",
        "24 JUN •••• 0221 Mercadolivre*Mercadol R$ 94,93",
        "27 JUN •••• 6560 Ifd*Ifood Club R$ 12,90",
        "30 JUN •••• 0941 Drogaria Pacheco R$ 65,57",
        "02 JUL •••• 7052 Netflix Entretenimento R$ 44,90",
        "02 JUL •••• 7052 Dm*Helphbomaxcom R$ 22,45",
        "03 JUL •••• 8072 Amazonmktplc*Casaaladi - Parcela 1/2 R$ 149,08",
        "Pagamentos -R$ 448,99",
        "10 JUN Pagamento em 10 JUN −R$ 448,99"
    ]
    current_datetime = utcnow()
    result = _extract_transaction_year(lines)
    assert result == current_datetime.year
    
def test_parse_expenses_without_month_in_one() -> None:
    lines = [
        "Data de vencimento: 13 JUL 2026",
        "fatura no valor de R$ 541,62",
        "Fatura anterior R$ 448,99",
        "Pagamentos -R$ 448,99",
        "10 JUN Pagamento em 10 JUN −R$ 448,99",
        "TRANSAÇÕES DE 04 JUN A 04 JUL",
        "Jorge L V S Filho R$ 541,62",
        "04 JUN •••• 0941 Dl*Google Google R$ 9,99",
        "11 ALA •••• 8072 Amazon R$ 72,18",
        "Pagamentos -R$ 448,99",
        "10 JUN Pagamento em 10 JUN −R$ 448,99",
    ]

    result = parse_expenses(lines)
    assert len(result) == 1

def test_build_parsed_pdf_expenses_with_default_parsed_date() -> None:
    result = build_parsed_pdf_expenses(
        year=2026,
        month=6,
        expenses=[
            {
                "date": "XX/YY",
                "payee": "TESTE",
                "amount": 10.0,
                "category": None,
                "current_installment": 1,
                "total_of_installments": 1,
            },
            {
                "date": "XX/YY",
                "payee": "TESTE 2",
                "amount": 20.0,
                "category": None,
                "current_installment": 1,
                "total_of_installments": 1,
            }
        ]
    )
    fallback_date = date(2026, 6, 1)
    assert len(result) == 2
    assert result[0].date == fallback_date
    assert result[1].date == fallback_date