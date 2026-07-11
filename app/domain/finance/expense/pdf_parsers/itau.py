import re
from datetime import date

from app.domain.finance.allocation.schema import AllocationSchema
from app.domain.finance.expense.pdf_parsers.schemas import (
    ParsedPDFSchema,
    ParsedPDFExpenseSchema,
)
from app.domain.finance.expense.pdf_parsers.utils import get_date, get_number, get_number_money, parse_amount
from app.models import utcnow, BankEnum

EXPENSE_PATTERN = re.compile(
    r"(?P<date>\d{2}/\d{2})\s+"
    r"(?P<payee>.*?)\s+"
    r"(?:(?P<current_installment>\d{2})/(?P<total_of_installments>\d{2})\s+)?"
    r"(?P<amount>-?\d{1,3}(?:\.\d{3})*,\d{2})"
)

IGNORE_ESTABLISHMENT_TOKENS = (
    "pagamento via conta",
    "total dos pagamentos",
    "lancamentos no cartao",
)

CATEGORY_KEYWORD_PATTERN = re.compile(
    r"(?i)\b(supermercado|restaurante|sa[úu]de|health|outros|vestu[áa]rio)\b"
)
STOP_CATEGORY_TOKENS = {
    "encargos",
    "juros",
    "multa",
    "iof",
    "valor",
    "limite",
    "ao",
    "operação",
    "operacao",
    "contratação",
    "contratacao",
    "simulação",
    "simulacao",
    "fique",
    "%",
}

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
        if "Total da fatura anterior" in line:
            previous_bill_total = get_number(line)
        if "Pagamento efetuado em" in line:            
            previous_bill_due_date = get_date(line)
        if "O total da sua fatura é:" in line:
            text = lines[index + 1].strip()
            bill_total = get_number_money(text)
        if "Vencimento:" in line:
            bill_due_date = get_date(line)
        if "Emissão:" in line:
            date_of_issue = get_date(line)
            year = date_of_issue.year if date_of_issue else year
            month = date_of_issue.month if date_of_issue else month

    return {
        "year": year,
        "month": month,
        "bill_total": bill_total,
        "bill_due_date": bill_due_date,
        "date_of_issue": date_of_issue,
        "previous_bill_total": previous_bill_total,
        "previous_bill_due_date": previous_bill_due_date
    }

def _clean_establishment(establishment: str) -> str:
    value = " ".join(establishment.split()).strip()
    if value.endswith("BRASILIA"):
        value = value[: -len("BRASILIA")].strip()
    if value.endswith(" do"):
        value = value[:-3].strip()
    return value

def _build_expense(match: re.Match[str]) -> dict:
    group_map = match.groupdict()
    current_installment_value = group_map.get("current_installment")
    total_of_installments_value = group_map.get("total_of_installments")
    current_installment = int(current_installment_value) if current_installment_value else 1
    total_of_installments = int(total_of_installments_value) if total_of_installments_value else 1
    return {
        "date": match.group("date"),
        "payee": _clean_establishment(match.group("payee")),
        "total_of_installments": total_of_installments,
        "current_installment": current_installment,
        "amount": parse_amount(match.group("amount")),
        "category": None,
    }

def _is_ignored_establishment(establishment: str) -> bool:
    normalized = establishment.lower()
    return any(token in normalized for token in IGNORE_ESTABLISHMENT_TOKENS)

def _extract_categories(line: str) -> list[str]:
    matches = list(CATEGORY_KEYWORD_PATTERN.finditer(line.strip()))
    if not matches:
        return []

    categories: list[str] = []
    for index, match in enumerate(matches):
        category_type = match.group(1)
        segment_end = matches[index + 1].start() if index + 1 < len(matches) else len(line)
        suffix = line[match.end() : segment_end].strip()
        category_tokens: list[str] = []
        for token in suffix.split():
            token_normalized = token.strip(".,:;").lower()
            if (
                not token_normalized
                or token_normalized in STOP_CATEGORY_TOKENS
                or any(char.isdigit() for char in token_normalized)
            ):
                break
            category_tokens.append(token.strip(".,:;"))
            if len(category_tokens) == 4:
                break

        if category_tokens:
            categories.append(f"{category_type} {' '.join(category_tokens)}".strip())
    return categories

def _extract_expenses_from_section(lines: list[str], start_index: int, end_index: int) -> list[dict]:
    if start_index < 0 or end_index <= start_index:
        return []

    expenses = []
    section_lines = lines[start_index:end_index]
    pending_without_category: list[int] = []

    def _flush_category_buffer(category_buffer: list[str]) -> None:
        nonlocal pending_without_category
        assign_count = min(len(category_buffer), len(pending_without_category))
        if assign_count == 0:
            category_buffer.clear()
            return

        target_indexes = pending_without_category[-assign_count:]
        categories_to_apply = category_buffer[-assign_count:]
        for expense_index, category in zip(target_indexes, categories_to_apply):
            expenses[expense_index]["category"] = category

        assigned_set = set(target_indexes)
        pending_without_category = [
            expense_index
            for expense_index in pending_without_category
            if expense_index not in assigned_set
        ]
        category_buffer.clear()

    category_buffer: list[str] = []
    for line in section_lines:
        normalized_line = line.replace("Lançamentos: compras e saques", "").strip()
        if not normalized_line:
            continue
        matches = list(EXPENSE_PATTERN.finditer(normalized_line))
        if matches and category_buffer:
            _flush_category_buffer(category_buffer)

        for match in matches:
            expense = _build_expense(match)
            if _is_ignored_establishment(expense["payee"]):
                continue
            expenses.append(expense)
            pending_without_category.append(len(expenses) - 1)

        categories = _extract_categories(normalized_line)
        if not categories:
            continue
        category_buffer.extend(categories)
        if matches:
            _flush_category_buffer(category_buffer)

    if category_buffer:
        _flush_category_buffer(category_buffer)
    return expenses

def _extract_products_and_services(lines: list[str]) -> list[dict]:
    section_start = -1
    section_end = len(lines)
    for index, line in enumerate(lines):
        if "Lançamentos: produtos e serviços" in line:
            section_start = index + 1
            continue
        if section_start != -1 and "Lançamentos produtos e serviços" in line:
            section_end = index
            break

    if section_start == -1:
        return []

    section_lines = lines[section_start:section_end]
    expenses = []
    for index, line in enumerate(section_lines):
        match = re.search(
            r"^(?P<date>\d{2}/\d{2})\s+"
            r"(?P<payee>.*?)\s+"
            r"(?P<amount>-?\d{1,3}(?:\.\d{3})*,\d{2})$",
            line.strip(),
        )
        if not match:
            continue
        expense = _build_expense(match)
        if index + 1 < len(section_lines):
            next_line = section_lines[index + 1].strip()
            if next_line and not re.match(r"^\d{2}/\d{2}\s+", next_line):
                expense["category"] = next_line
        expenses.append(expense)
    return expenses

def _sort_expenses(expenses: list[dict]) -> list[dict]:
    def _sort_key(expense: dict) -> tuple[int, int]:
        day, month = expense["date"].split("/")
        return int(month), int(day)

    return sorted(expenses, key=_sort_key)

def parse_expenses(lines: list[str]) -> list[dict]:
    start_section = -1
    end_section = len(lines)
    for index, line in enumerate(lines):
        if "Lançamentos: compras e saques" in line and start_section == -1:
            start_section = index
            continue
        if "Lançamentos: produtos e serviços" in line and start_section != -1:
            end_section = index
            break
    
    purchases = _extract_expenses_from_section(
        lines=lines,
        end_index=end_section,
        start_index=start_section,        
    )
    products_and_services = _extract_products_and_services(lines)
    return _sort_expenses(purchases + products_and_services)

def build_parsed_pdf_expenses(year: int, month: int, expenses: list[dict]) -> list[ParsedPDFExpenseSchema]:
    parsed_list: list[ParsedPDFExpenseSchema] = []
    for expense in expenses:
        parsed_date = get_date(f"{expense["date"]}/{year}")
        if parsed_date is None:
            parsed_date = date(year, month, 1)

        reference_month = parsed_date.month
        parsed = ParsedPDFExpenseSchema(
            date=parsed_date,
            payee=expense["payee"],
            amount=expense["amount"],
            category=expense["category"],
            reference_month=reference_month,
            current_installment=expense["current_installment"],
            total_of_installments=expense["total_of_installments"],
        )
        parsed_list.append(parsed)

    return parsed_list

def parse_itau(
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

    return ParsedPDFSchema(
        year=year,
        bank=BankEnum.ITAU,
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