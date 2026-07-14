from collections import defaultdict
from datetime import datetime
import io

import pdfplumber

from app.domain.finance.allocation.schema import AllocationSchema
from app.domain.finance.expense.pdf_parsers.itau import parse_itau
from app.domain.finance.expense.pdf_parsers.nubank import parse_nubank
from app.domain.finance.expense.pdf_parsers.schema import ParsedPDFSchema
from app.domain.finance.months.schema import PayloadMonthPersistSchema
from app.models import BankEnum, Allocation, Expense


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
            bank=bank,
            error=True,
            message=f"Not implemented yet for bank: {bank.value}",
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
            return parse_nubank(
                lines=lines,
                allocation=allocation_schema,
                reference_year=reference_year,
                reference_month=reference_month,
            )
        case BankEnum.CAIXA:
            return fallback_result
        
def generate_months_by_year(expenses: list[Expense]) -> dict[int, list[PayloadMonthPersistSchema]]:
    months_aggregated: dict[tuple[int, int], dict] = defaultdict(
        lambda: {"amount": 0.0, "status": None}
    )

    years_found: set[int] = set()

    for expense in expenses:
        for month in expense.months:
            amount = float(month.amount)
            years_found.add(month.reference_year)
            key = (month.reference_year, month.reference_month)
            months_aggregated[key]["amount"] += amount
            if months_aggregated[key]["status"] is None:
                months_aggregated[key]["status"] = month.status
                    
    
    result: dict[int, list[PayloadMonthPersistSchema]] = {}

    for year in sorted(years_found):
        result[year] = []
        for month_num in range(1, 13):
            key = (year, month_num)
            data = months_aggregated.get(key, {"amount": 0.0, "status": None})
            result[year].append(
                PayloadMonthPersistSchema(
                    amount=data["amount"],
                    status=data["status"],
                    reference_month=month_num,
                )
            )

    return result