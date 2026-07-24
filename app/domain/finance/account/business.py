from decimal import Decimal
from collections.abc import Iterable

from app.domain.finance.account.schema import PayloadAccountCreateSchema
from app.models import AccountTypeEnum


def sum_amounts(amounts: Iterable[Decimal]) -> Decimal:
    return sum(amounts, Decimal("0.00"))


def sum_expenses_by_status(expenses: list, status: str) -> Decimal:
    return sum_amounts(
        month["amount"]
        for obj in expenses
        for month in obj.get("months", [])
        if month.get("status") == status
    )

DEFAULT_ACCOUNTS: list[PayloadAccountCreateSchema] = [
    PayloadAccountCreateSchema(
        name="Nubank",
        type=AccountTypeEnum.BANK,
        initial_balance=0.0,
    ),
    PayloadAccountCreateSchema(
        name="Itaú",
        type=AccountTypeEnum.BANK,
        initial_balance=0.0,
    ),
    PayloadAccountCreateSchema(
        name="Caixa",
        type=AccountTypeEnum.BANK,
        initial_balance=0.0,
    )
]