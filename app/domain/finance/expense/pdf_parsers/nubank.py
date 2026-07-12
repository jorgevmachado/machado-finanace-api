import re
from datetime import date

from app.domain.finance.allocation.schema import AllocationSchema
from app.domain.finance.expense.pdf_parsers.schema import (
    ParsedPDFSchema,
    ParsedPDFExpenseSchema,
)
from app.domain.finance.expense.pdf_parsers.utils import (
    get_date_with_named_month,
    get_date_with_named_month_without_year,
    get_number_money,
    parse_amount,
)
from app.models import utcnow, BankEnum

MONTHS = {
    "JAN": 1,
    "FEV": 2,
    "MAR": 3,
    "ABR": 4,
    "MAI": 5,
    "JUN": 6,
    "JUL": 7,
    "AGO": 8,
    "SET": 9,
    "OUT": 10,
    "NOV": 11,
    "DEZ": 12,
}

TRANSACTION_PATTERN = re.compile(
    r"^(?P<day>\d{2})\s+(?P<month>[A-Z]{3})\s+•{4}\s+\d{4}\s+"
    r"(?P<payee>.*?)\s+R\$\s*(?P<amount>\d{1,3}(?:\.\d{3})*,\d{2})$"
)
INSTALLMENT_PATTERN = re.compile(r"\s*-\s*Parcela\s+(?P<current>\d+)/(?P<total>\d+)\s*$")


def parse_header(lines: list[str]) -> dict:
    current_datetime = utcnow()
    year = current_datetime.year
    month = current_datetime.month
    bill_total = 0
    date_of_issue = None
    bill_due_date = None
    previous_bill_total = 0

    previous_bill_due_date = None

    for index, line in enumerate(lines):
        if "Data de vencimento" in line:
            bill_due_date = get_date_with_named_month(line)
        if "fatura no valor de" in line:            
            bill_total = get_number_money(line)
        if "EMISSÃO E ENVIO" in  line:
            date_of_issue = get_date_with_named_month(line)
            year = date_of_issue.year if date_of_issue else year
            month = date_of_issue.month if date_of_issue else month
        if "Fatura anterior" in line:
            previous_bill_total = get_number_money(line)
        if "Pagamentos -" in line:
            text = lines[index + 1].strip()
            previous_bill_due_date = get_date_with_named_month_without_year(text, year)
    return {
        "year": year,
        "month": month,
        "bill_total": bill_total,
        "bill_due_date": bill_due_date,
        "date_of_issue": date_of_issue,
        "previous_bill_total": previous_bill_total,
        "previous_bill_due_date": previous_bill_due_date,
    }


def _extract_transaction_year(lines: list[str]) -> int:
    current_year = utcnow().year
    for line in lines:
        match = re.search(r"EMISSÃO E ENVIO\s+\d{2}\s+[A-Z]{3}\s+(?P<year>\d{4})", line)
        if match:
            return int(match.group("year"))
    return current_year


def _extract_installments(payee: str) -> tuple[str, int, int]:
    match = INSTALLMENT_PATTERN.search(payee)
    if not match:
        return payee.strip(), 1, 1

    clean_payee = payee[: match.start()].strip()
    current = int(match.group("current"))
    total = int(match.group("total"))
    return clean_payee, current, total


def parse_expenses(lines: list[str]) -> list[dict]:
    year = _extract_transaction_year(lines)
    expenses: list[dict] = []
    in_transactions_section = False

    for line in lines:
        clean_line = line.strip()
        if "TRANSAÇÕES DE" in clean_line:
            in_transactions_section = True
            continue
        if in_transactions_section and clean_line.startswith("Pagamentos"):
            break
        if not in_transactions_section:
            continue

        match = TRANSACTION_PATTERN.match(clean_line)
        if not match:
            continue

        month_name = match.group("month")
        month = MONTHS.get(month_name)
        if month is None:
            continue

        day = int(match.group("day"))
        expense_date = date(year, month, day)
        payee, current_installment, total_of_installments = _extract_installments(
            match.group("payee")
        )
        expenses.append(
            {
                "date": expense_date.isoformat(),
                "payee": payee,
                "total_of_installments": total_of_installments,
                "current_installment": current_installment,
                "amount": parse_amount(match.group("amount")),
                "category": "OTHERS",
                "reference_month": expense_date.month,
            }
        )

    return expenses


def build_parsed_pdf_expenses(
    year: int,
    month: int,
    expenses: list[dict],
) -> list[ParsedPDFExpenseSchema]:
    parsed_list: list[ParsedPDFExpenseSchema] = []
    fallback_date = date(year, month, 1)
    for expense in expenses:
        try:
            parsed_date = date.fromisoformat(expense["date"])
        except ValueError:
            parsed_date = fallback_date

        parsed_list.append(
            ParsedPDFExpenseSchema(
                date=parsed_date,
                payee=expense["payee"],
                amount=expense["amount"],
                category=expense["category"],
                reference_month=expense.get("reference_month", parsed_date.month),
                current_installment=expense["current_installment"],
                total_of_installments=expense["total_of_installments"],
            )
        )
    return parsed_list

def parse_nubank(
        lines: list[str],
        allocation: AllocationSchema,
        reference_year: int | None = None,
        reference_month: int | None = None
) -> ParsedPDFSchema:
    error = False
    message = "Create Successfully!"
    
    header = parse_header(lines)

    parsed_expenses = parse_expenses(lines)
    
    year = reference_year or header["year"]
    month = reference_month or header["month"]
    
    if reference_year and reference_year != header["year"]:
        error = True
        message = "Reference year is different from document"

    if reference_month and reference_month != header["month"]:
        error = True
        message = "Reference month is different from document"

    expenses = build_parsed_pdf_expenses(year, month, parsed_expenses)

    if len(expenses) == 0:
        error = True
        message = "No expenses found in the document"

    return ParsedPDFSchema(
            bank=BankEnum.NUBANK,
            error=error,
            message=message,
            expenses=expenses,
            allocation=allocation,
            bill_total=header["bill_total"],
            bill_due_date=header["bill_due_date"],
            date_of_issue=header["date_of_issue"],
            reference_year=year,
            reference_month=month,
            previous_bill_total=header["previous_bill_total"],
            previous_bill_due_date=header["previous_bill_due_date"],
        )
