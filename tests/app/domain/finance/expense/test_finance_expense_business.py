from app.domain.finance.expense.business import get_expense_months, get_expense_children
from app.domain.finance.schema import (
    PayloadFinanceExpensePersistSchema,
    PayloadFinanceChildrenExpensePersistSchema,
)
from app.models import CategoryTypeEnum


class TestFinanceExpenseGetExpenseMonthsBusiness:
    @staticmethod
    def test_finance_expense_get_expense_months_business_with_type_credit_card():
        payloads = [
            PayloadFinanceExpensePersistSchema(
                amount=1000.00,
                children=[
                    PayloadFinanceChildrenExpensePersistSchema(
                        name="name-1",
                        type=CategoryTypeEnum.ENTERTAINMENT,
                        amount=100.00,
                        description="description-1",
                    ),
                    PayloadFinanceChildrenExpensePersistSchema(
                        name="name-2",
                        type=CategoryTypeEnum.ENTERTAINMENT,
                        amount=200.00,
                        description="description-2",
                    ),
                ],
            ),
            PayloadFinanceExpensePersistSchema(
                amount=2000.00,
                reference_month=2,
                children=[
                    PayloadFinanceChildrenExpensePersistSchema(
                        name="name-3",
                        type=CategoryTypeEnum.ENTERTAINMENT,
                        amount=300.00,
                        description="description-1",
                    ),
                    PayloadFinanceChildrenExpensePersistSchema(
                        name="name-4",
                        type=CategoryTypeEnum.ENTERTAINMENT,
                        amount=400.00,
                        description="description-2",
                    ),
                ],
            ),
        ]
        result = get_expense_months(payloads, CategoryTypeEnum.CREDIT_CARD)
        assert len(result) == 1

    @staticmethod
    def test_finance_expense_get_expense_months_business_without_type_credit_card():
        payloads = [
            PayloadFinanceExpensePersistSchema(
                amount=1000.00,
                reference_month=1,
                children=[
                    PayloadFinanceChildrenExpensePersistSchema(
                        name="name-1",
                        type=CategoryTypeEnum.ENTERTAINMENT,
                        amount=100.00,
                        description="description-1",
                    ),
                    PayloadFinanceChildrenExpensePersistSchema(
                        name="name-2",
                        type=CategoryTypeEnum.ENTERTAINMENT,
                        amount=200.00,
                        description="description-2",
                    ),
                ],
            ),
            PayloadFinanceExpensePersistSchema(
                amount=2000.00,
                reference_month=2,
                children=[
                    PayloadFinanceChildrenExpensePersistSchema(
                        name="name-3",
                        type=CategoryTypeEnum.ENTERTAINMENT,
                        amount=300.00,
                        description="description-1",
                    ),
                    PayloadFinanceChildrenExpensePersistSchema(
                        name="name-4",
                        type=CategoryTypeEnum.ENTERTAINMENT,
                        amount=400.00,
                        description="description-2",
                    ),
                ],
            ),
        ]
        result = get_expense_months(payloads, CategoryTypeEnum.ENTERTAINMENT)
        assert len(result) == 2


class TestFinanceExpenseGetExpenseChildrenBusiness:
    @staticmethod
    def test_finance_expense_get_expense_children_without_type_credit_card():
        payloads = [
            PayloadFinanceExpensePersistSchema(
                amount=1000.00,
                children=[
                    PayloadFinanceChildrenExpensePersistSchema(
                        name="name-1",
                        type=CategoryTypeEnum.ENTERTAINMENT,
                        amount=100.00,
                        description="description-1",
                    ),
                    PayloadFinanceChildrenExpensePersistSchema(
                        name="name-2",
                        type=CategoryTypeEnum.ENTERTAINMENT,
                        amount=200.00,
                        description="description-2",
                    ),
                ],
            ),
            PayloadFinanceExpensePersistSchema(
                amount=2000.00,
                reference_month=2,
                children=[
                    PayloadFinanceChildrenExpensePersistSchema(
                        name="name-3",
                        type=CategoryTypeEnum.ENTERTAINMENT,
                        amount=300.00,
                        description="description-1",
                    ),
                    PayloadFinanceChildrenExpensePersistSchema(
                        name="name-4",
                        type=CategoryTypeEnum.ENTERTAINMENT,
                        amount=400.00,
                        description="description-2",
                    ),
                ],
            ),
        ]
        result = get_expense_children(payloads, CategoryTypeEnum.ENTERTAINMENT)
        assert len(result) == 0

    @staticmethod
    def test_finance_expense_get_expense_children_with_type_credit_card():
        payloads = [
            PayloadFinanceExpensePersistSchema(
                amount=1000.00,
                children=[
                    PayloadFinanceChildrenExpensePersistSchema(
                        name="name-1",
                        type=CategoryTypeEnum.ENTERTAINMENT,
                        amount=100.00,
                        description="description-1",
                    ),
                    PayloadFinanceChildrenExpensePersistSchema(
                        name="name-2",
                        type=CategoryTypeEnum.ENTERTAINMENT,
                        amount=200.00,
                        description="description-2",
                    ),
                ],
            ),
            PayloadFinanceExpensePersistSchema(
                amount=3000.00,
                reference_month=2,
            ),
            PayloadFinanceExpensePersistSchema(
                amount=4000.00,
                reference_month=3,
                children=[
                    PayloadFinanceChildrenExpensePersistSchema(
                        name="name-3",
                        type=CategoryTypeEnum.ENTERTAINMENT,
                        amount=300.00,
                        description="description-1",
                    ),
                    PayloadFinanceChildrenExpensePersistSchema(
                        name="name-4",
                        type=CategoryTypeEnum.ENTERTAINMENT,
                        amount=400.00,
                        description="description-2",
                    ),
                ],
            ),
        ]
        result = get_expense_children(payloads, CategoryTypeEnum.CREDIT_CARD)
        assert len(result) == 1
