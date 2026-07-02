from datetime import datetime

from app.models import MonthStatusEnum, utcnow


def validate_paid_at(
    status: MonthStatusEnum, paid_at: datetime | None = None
) -> datetime | None:
    if status == MonthStatusEnum.PAID and not paid_at:
        return utcnow()
    if status != MonthStatusEnum.PAID and paid_at:
        return None
    return paid_at


def get_status(
    status: MonthStatusEnum | None = MonthStatusEnum.PENDING,
    paid_at: datetime | None = None,
    reference_month: int | None = None,
) -> MonthStatusEnum:
    current_date = utcnow()
    current_month = current_date.month

    if reference_month is not None and status != MonthStatusEnum.PAID:
        return (
            MonthStatusEnum.PAID
            if reference_month <= current_month
            else MonthStatusEnum.PENDING
        )

    if paid_at is not None and status != MonthStatusEnum.PAID:
        paid_at_with_tz = (
            paid_at.replace(tzinfo=current_date.tzinfo)
            if paid_at.tzinfo is None
            else paid_at
        )
        return (
            MonthStatusEnum.PAID
            if paid_at_with_tz <= current_date
            else MonthStatusEnum.PENDING
        )

    return status
