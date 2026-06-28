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
