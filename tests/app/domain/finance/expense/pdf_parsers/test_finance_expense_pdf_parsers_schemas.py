from datetime import date, datetime
from uuid import uuid4

from app.domain.finance.allocation.schema import AllocationSchema
from app.domain.finance.expense.pdf_parsers.schema import (
    ParsedPDFExpenseSchema,
    ParsedPDFSchema,
)
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


def test_parsed_pdf_expense_schema() -> None:
    expense = ParsedPDFExpenseSchema(
        date=date(2026, 7, 7),
        payee="DOG DO RAFILDSBRASILIAB",
        amount=70.0,
        category="supermercado BRASILIA",
        reference_month=7,
        current_installment=1,
        total_of_installments=1,
        all_installments_paid=False
    )

    assert expense.payee == "DOG DO RAFILDSBRASILIAB"
    assert expense.amount == 70.0
    assert expense.reference_month == 7


def test_parsed_pdf_schema() -> None:
    allocation = _allocation_schema()
    result = ParsedPDFSchema(
        year=2026,
        bank=BankEnum.ITAU,
        error=False,
        message="Create Successfully!",
        expenses=[],
        allocation=allocation,
        bill_total=4022.54,
        bill_due_date=date(2026, 7, 15),
        date_of_issue=date(2026, 7, 8),
        reference_year=2026,
        reference_month=7,
        previous_bill_total=3650.94,
        previous_bill_due_date=date(2026, 6, 10),
    )

    assert result.bank == BankEnum.ITAU
    assert result.allocation.id == allocation.id
    assert result.bill_total == 4022.54
