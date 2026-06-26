from decimal import Decimal
from collections.abc import Iterable

from app.models import Transaction, TransactionStatusEnum

def sum_amounts(amounts: Iterable[Decimal]) -> Decimal:
    return sum(amounts, Decimal("0.00"))

def sum_transactions_by_status(
    transactions: list[Transaction],
    status: TransactionStatusEnum,
) -> Decimal:
    return sum_amounts(
        transaction.amount
        for transaction in transactions
        if transaction.status == status
    )

