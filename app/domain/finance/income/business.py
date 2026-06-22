from http import HTTPStatus

from fastapi import HTTPException

from app.models import utcnow


def validate_year(year: int) -> int:
    current_year = utcnow().year
    if year > current_year:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Reference year {year} must be less than or equal to the current year {current_year}",
        )
    return year

def validate_month(month: int) -> int:
    if month <= 0 or month > 12:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Reference month {month} must be between 1 and 12",
        )
    return month