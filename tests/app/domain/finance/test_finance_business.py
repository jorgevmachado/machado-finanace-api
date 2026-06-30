from __future__ import annotations

from app.domain.finance.business import merge_months_by_reference_month
from app.domain.finance.schema import FinanceCreateMonthSchema


class TestFinanceMergeMonthsByReferenceMonth:
    @staticmethod
    def test_finance_merge_months_by_reference_month():
        months: list[FinanceCreateMonthSchema] = [
            FinanceCreateMonthSchema(amount=1700.00, reference_day=7, reference_month=1),
            FinanceCreateMonthSchema(amount=1000.00, reference_day=6, reference_month=2),
            FinanceCreateMonthSchema(amount=1500.00, reference_day=9, reference_month=3),
            FinanceCreateMonthSchema(amount=1500.00, reference_day=10, reference_month=4),
            FinanceCreateMonthSchema(amount=1500.00, reference_day=8, reference_month=5),
            FinanceCreateMonthSchema(amount=300.00, reference_day=14, reference_month=5),
            FinanceCreateMonthSchema(amount=85.09, reference_day=14, reference_month=5),
            FinanceCreateMonthSchema(amount=1500.00, reference_day=5, reference_month=6),
            FinanceCreateMonthSchema(amount=300.00, reference_day=12, reference_month=6),
            FinanceCreateMonthSchema(amount=450.00, reference_day=16, reference_month=6),
        ]
        expected_result: list[FinanceCreateMonthSchema] = [
            FinanceCreateMonthSchema(amount=1700.00, reference_day=7, reference_month=1),
            FinanceCreateMonthSchema(amount=1000.00, reference_day=6, reference_month=2),
            FinanceCreateMonthSchema(amount=1500.00, reference_day=9, reference_month=3),
            FinanceCreateMonthSchema(amount=1500.00, reference_day=10, reference_month=4),
            FinanceCreateMonthSchema(amount=1885.09, reference_day=14, reference_month=5),
            FinanceCreateMonthSchema(amount=2250.00, reference_day=16, reference_month=6),
        ]
        result = merge_months_by_reference_month(months=months)
        assert result == expected_result