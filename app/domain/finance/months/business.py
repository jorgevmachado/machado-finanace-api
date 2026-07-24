from datetime import date, datetime

from app.domain.finance.months.schema import PayloadMonthPersistSchema
from app.models import utcnow, MonthStatusEnum


def complete_months_in_year(
    months: list[PayloadMonthPersistSchema],
    reference_year: int | None = None,
    reference_day: int = 10,
) -> list[PayloadMonthPersistSchema]:
    year = reference_year or utcnow().year
    months_provided = {item.reference_month for item in months}
    all_months = set(range(1, 13))
    missing_months = all_months - months_provided

    # Populate transaction_date for existing months if not already set
    for month in months:
        if month.transaction_date is None:
            month.transaction_date = date(year, month.reference_month, reference_day)
        if month.status is None:
            month.status = MonthStatusEnum.PENDING

    # Add missing months with amount=0.0
    for month in missing_months:
        months.append(
            PayloadMonthPersistSchema(
                amount=0.0,
                status=MonthStatusEnum.PENDING,
                reference_month=month,
                transaction_date=date(year, month, reference_day),
            )
        )
    months.sort(key=lambda x: x.reference_month)
    return months


def get_month_status(month: PayloadMonthPersistSchema) -> MonthStatusEnum:

    current_date = utcnow()
    current_month = current_date.month

    transaction_date = month.transaction_date

    if transaction_date is not None and month.status != MonthStatusEnum.PAID:
        transaction_datetime = datetime(
            year=transaction_date.year,
            month=transaction_date.month,
            day=transaction_date.day,
        )
        paid_at_with_tz = (
            transaction_datetime.replace(tzinfo=current_date.tzinfo)
            if transaction_datetime.tzinfo is None
            else transaction_datetime
        )
        return (
            MonthStatusEnum.PAID
            if paid_at_with_tz <= current_date
            else MonthStatusEnum.PENDING
        )

    if month.status:
        return (
            MonthStatusEnum.PAID
            if month.reference_month <= current_month
            else MonthStatusEnum.PENDING
        )

    return MonthStatusEnum.PENDING


def get_paid_at(
    status: MonthStatusEnum,
    transaction_date: date | None = None,
) -> datetime | None:
    if status == MonthStatusEnum.PAID and transaction_date is None:
        return utcnow()

    if status == MonthStatusEnum.PAID and transaction_date is not None:
        return datetime(
            year=transaction_date.year,
            month=transaction_date.month,
            day=transaction_date.day,
        )

    return None


def merge_months_by_month(
    months: list[PayloadMonthPersistSchema],
) -> list[PayloadMonthPersistSchema]:
    merged_months: dict[int, PayloadMonthPersistSchema] = {}
    for month in months:
        reference_month = month.reference_month
        if not reference_month:
            continue
        merged_month = merged_months.get(reference_month)
        if not merged_month:
            merged_months[reference_month] = month.model_copy()
            continue
        merged_month.amount += month.amount
        merged_month.reference_day = month.reference_day

    return list(merged_months.values())
