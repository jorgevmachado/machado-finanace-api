from app.domain.finance.schema import FinanceCreateMonthSchema


def merge_months_by_reference_month(
    months: list[FinanceCreateMonthSchema],
) -> list[FinanceCreateMonthSchema]:
    merged_months: dict[int, FinanceCreateMonthSchema] = {}
    for month in months:
        reference_month = month.reference_month
        merged_month = merged_months.get(reference_month)
        if not merged_month:
            merged_months[reference_month] = month.model_copy()
            continue

        merged_month.amount += month.amount
        merged_month.reference_day = month.reference_day

    return list(merged_months.values())
