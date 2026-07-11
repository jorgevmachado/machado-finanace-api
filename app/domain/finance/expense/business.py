from datetime import datetime
import io

import pdfplumber

from app.domain.finance.allocation.schema import AllocationSchema
from app.domain.finance.expense.pdf_parsers.itau import parse_itau
from app.domain.finance.expense.pdf_parsers.schemas import ParsedPDFSchema
from app.models import BankEnum, Allocation

def generate_lines_pdf(file) -> list[str]:
    text = ""
    with pdfplumber.open(io.BytesIO(file)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.splitlines()


def parse_pdf(
    file,
    bank: BankEnum,
    allocation: Allocation,
    reference_year:  int | None = None,
    reference_month: int | None = None
) -> ParsedPDFSchema:
    lines = generate_lines_pdf(file)
    allocation_schema = AllocationSchema.model_validate(allocation)
    fallback_result = ParsedPDFSchema(
            year=reference_year or datetime.now().year,
            bank=bank,
            error=True,
            message=f"Not implemented yet for bank: {bank}",
            expenses=[],
            allocation=allocation_schema,
            bill_total=0.0,
            bill_due_date=None,
            date_of_issue=None,
            reference_year=reference_year or datetime.now().year,
            reference_month=reference_month or datetime.now().month,
            previous_bill_total=0.0,
            previous_bill_due_date=None,
        )

    match bank:
        case BankEnum.ITAU:
            return parse_itau(
                lines=lines,
                allocation=allocation_schema,
                reference_year=reference_year,
                reference_month=reference_month,
            )
        case BankEnum.NUBANK:
            return fallback_result
        case BankEnum.CAIXA:
            return fallback_result