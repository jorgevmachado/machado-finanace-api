from datetime import datetime

from app.models import TransactionStatusEnum, utcnow


def validate_paid_at(status: TransactionStatusEnum, paid_at: datetime | None = None) -> datetime | None:
    if status == TransactionStatusEnum.PAID and not paid_at:
        return utcnow()
    if status != TransactionStatusEnum.PAID and paid_at:
        return None
    return paid_at
    