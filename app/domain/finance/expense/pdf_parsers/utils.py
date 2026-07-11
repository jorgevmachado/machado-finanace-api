import re
from datetime import date, datetime
from decimal import Decimal

MONTHS = {
    "JAN": "01",
    "FEB": "02",
    "MAR": "03",
    "APR": "04",
    "MAY": "05",
    "JUN": "06",
    "JUL": "07",
    "AUG": "08",
    "SEP": "09",
    "OCT": "10",
    "NOV": "11",
    "DEC": "12",
}

def get_date_with_named_month(value: str) -> date | None:
    match = re.search(r"(\d{2})\s+([A-Z]{3})\s+(\d{4})", value)
    if match:
        day = match.group(1)
        month = MONTHS[match.group(2)]
        year = match.group(3)

        return datetime.strptime(f"{day}/{month}/{year}", "%d/%m/%Y").date()
    return None

def get_date_with_named_month_without_year(value: str, reference_year: int) -> date | None:
    match = re.search(r"(\d{1,2})\s+([A-Z]{3})", value.upper())

    if not match:
        return None

    day = int(match.group(1))
    month = int(MONTHS[match.group(2)])

    return date(reference_year, month, day)

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