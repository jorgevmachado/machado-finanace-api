from datetime import date


def get_received_at(
        year: int,
        month: int,
        day: int
):
    return date(year, month, day)