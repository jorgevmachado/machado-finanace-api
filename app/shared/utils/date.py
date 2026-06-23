import calendar


def generate_description(
    month: int,
    source: str,
    description: str | None = None,
    item_description: str | None = None,
) -> str:
    if description and not item_description:
        return description

    month_name = get_month_name(month)

    if item_description and not description:
        return f"{item_description} | {month_name}"

    return f"{source} | {month_name}"


def get_month_name(month: int) -> str:
    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12")
    return calendar.month_name[month]


def get_valid_day(year: int, month: int, day: int | None = None) -> int:
    first_day, last_day = calendar.monthrange(year, month)
    if day is None:
        return first_day

    if day > last_day:
        return last_day

    if day < first_day:
        return first_day

    return day
