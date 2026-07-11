import re
from datetime import date, datetime
from decimal import Decimal


def get_date(value: str) -> date | None:
    match = re.search(r"\d{2}/\d{2}/\d{4}", value)
    if match:        
        date_str = match.group(0)
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    return None

def get_number(value: str) -> Decimal:
    match = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})", value)
    if match:
        return Decimal(match.group(1).replace(".", "").replace(",", "."))
    return Decimal(0)

def get_number_money(value: str) -> Decimal:
    match = re.search(r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})", value)
    if match:
        return Decimal(match.group(1).replace(".", "").replace(",", "."))
    return Decimal(0)


def parse_amount(amount_value: str) -> float:
    return float(amount_value.replace(".", "").replace(",", "."))