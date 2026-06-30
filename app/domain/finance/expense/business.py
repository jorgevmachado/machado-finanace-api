from datetime import datetime

from app.models import ExpenseStatusEnum, utcnow


def validate_paid_at(
    status: ExpenseStatusEnum, paid_at: datetime | None = None
) -> datetime | None:
    if status == ExpenseStatusEnum.PAID and not paid_at:
        return utcnow()
    if status != ExpenseStatusEnum.PAID and paid_at:
        return None
    return paid_at


def get_status(
    status: ExpenseStatusEnum,
    paid_at: datetime | None = None,
    reference_month: int | None = None,
) -> ExpenseStatusEnum:
    current_date = utcnow()
    current_month = current_date.month

    if reference_month is not None and status != ExpenseStatusEnum.PAID:
        return (
            ExpenseStatusEnum.PAID
            if reference_month <= current_month
            else ExpenseStatusEnum.PENDING
        )

    if paid_at is not None and status != ExpenseStatusEnum.PAID:
        paid_at_with_tz = (
            paid_at.replace(tzinfo=current_date.tzinfo)
            if paid_at.tzinfo is None
            else paid_at
        )
        return (
            ExpenseStatusEnum.PAID
            if paid_at_with_tz <= current_date
            else ExpenseStatusEnum.PENDING
        )

    return status
