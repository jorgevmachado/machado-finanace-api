from app.domain.finance.expense_month.schema import PayloadExpenseMonthPersistSchema


def merge_months_by_reference_month(
    months: list[PayloadExpenseMonthPersistSchema],
) -> list[PayloadExpenseMonthPersistSchema]:
    merged_months: dict[int, PayloadExpenseMonthPersistSchema] = {}
    for month in months:
        reference_month = month.reference_month
        merged_month = merged_months.get(reference_month)
        if not merged_month:
            merged_months[reference_month] = month.model_copy()
            continue

        merged_month.amount += month.amount
        merged_month.reference_day = month.reference_day

    return list(merged_months.values())


def has_yearly_data(finance) -> bool:
    incomes = getattr(finance, "incomes", []) or []
    expenses = getattr(finance, "expenses", []) or []
    allocation_contributions = getattr(finance, "allocation_contributions", []) or []
    allocations = getattr(finance, "allocations", []) or []
    return any(
        [
            len(incomes) > 0,
            len(expenses) > 0,
            len(allocation_contributions) > 0,
            len(allocations) > 0,
        ]
    )
