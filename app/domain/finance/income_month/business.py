from datetime import date

def validate_received_at(
    day: int,
    year: int,
    month: int,
    received_at: date | None = None
) -> date:
    if received_at is not None:
        return received_at
    return date(year, month, day)