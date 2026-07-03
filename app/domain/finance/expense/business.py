from app.domain.finance.expense.schema import (
    PayloadFinanceExpensePersistRequiredSchema,
    PayloadFinanceExpensePersistChildrenRequiredSchema,
)
from app.domain.finance.months.business import merge_months_by_month
from app.domain.finance.months.schema import PayloadMonthPersistSchema
from app.domain.finance.schema import PayloadFinanceExpensePersistSchema
from app.models import CategoryTypeEnum


def get_expense_months(
    payloads: list[PayloadFinanceExpensePersistSchema],
    category_type: CategoryTypeEnum,
) -> list[PayloadMonthPersistSchema]:
    if category_type != CategoryTypeEnum.CREDIT_CARD:
        return merge_months_by_month(payloads or [])
    parent_expense_months: list[PayloadMonthPersistSchema] = []
    for payload in payloads or []:
        if not payload.reference_month:
            continue
        parent_expense_months.append(
            PayloadMonthPersistSchema(
                amount=payload.amount,
                reference_month=payload.reference_month,
            )
        )
    return parent_expense_months


def get_expense_children(
    payloads: list[PayloadFinanceExpensePersistSchema],
    category_type: CategoryTypeEnum,
) -> list[PayloadFinanceExpensePersistRequiredSchema]:
    if category_type != CategoryTypeEnum.CREDIT_CARD:
        return []

    expense_children: list[PayloadFinanceExpensePersistRequiredSchema] = []
    for payload in payloads or []:
        if not payload.reference_month:
            continue
        if not payload.children:
            continue
        expense_children.append(
            PayloadFinanceExpensePersistRequiredSchema(
                children=[
                    PayloadFinanceExpensePersistChildrenRequiredSchema(
                        name=item.name,
                        type=item.type,
                        amount=item.amount,
                        description=item.description,
                        reference_day=item.reference_day,
                        reference_month=payload.reference_month,
                    )
                    for item in payload.children
                ],
                reference_month=payload.reference_month,
            )
        )

    return expense_children
