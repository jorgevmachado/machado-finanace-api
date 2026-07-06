from datetime import date, datetime

from app.domain.finance.months.business import (
    complete_months_in_year,
    get_month_status,
    get_paid_at,
    merge_months_by_month,
)
from app.domain.finance.months.schema import PayloadMonthPersistSchema
from app.models import MonthStatusEnum, utcnow


class TestFinanceMonthsCompleteMonthInYear:
    @staticmethod
    def test_finance_months_complete_month_in_year_empty():
        payload_months: list[PayloadMonthPersistSchema] = []
        result = complete_months_in_year(months=payload_months)
        assert len(result) == 12
        assert all(month.amount == 0.0 for month in result)

    @staticmethod
    def test_finance_months_complete_month_in_year_not_empty():
        payload_months: list[PayloadMonthPersistSchema] = [
            PayloadMonthPersistSchema(amount=1000.00, reference_month=1),
            PayloadMonthPersistSchema(amount=2000.00, reference_month=2),
        ]
        result = complete_months_in_year(months=payload_months)
        assert len(result) == 12
        assert all(
            month.amount == 1000.00 or month.amount == 2000.00 or month.amount == 0.0
            for month in result
        )
        assert all(month.amount in [1000.00, 2000.00, 0.0] for month in result)

    @staticmethod
    def test_finance_months_complete_month_in_year_with_reference_year_and_day():
        payload_months: list[PayloadMonthPersistSchema] = [
            PayloadMonthPersistSchema(amount=1000.00, reference_month=1),
            PayloadMonthPersistSchema(amount=2000.00, reference_month=2),
        ]
        result = complete_months_in_year(
            months=payload_months, reference_year=2023, reference_day=15
        )
        assert len(result) == 12
        assert all(
            month.amount == 1000.00 or month.amount == 2000.00 or month.amount == 0.0
            for month in result
        )
        assert all(month.amount in [1000.00, 2000.00, 0.0] for month in result)
        assert all(month.transaction_date.year == 2023 for month in result)
        assert all(month.transaction_date.day == 15 for month in result)
        assert all(month.status == MonthStatusEnum.PENDING for month in result)

    @staticmethod
    def test_finance_months_complete_month_in_year_with_status():
        payload_months: list[PayloadMonthPersistSchema] = [
            PayloadMonthPersistSchema(
                amount=1000.00, reference_month=1, status=MonthStatusEnum.PAID
            ),
            PayloadMonthPersistSchema(
                amount=2000.00, reference_month=2, status=MonthStatusEnum.CANCELLED
            ),
        ]
        result = complete_months_in_year(
            months=payload_months, reference_year=2023, reference_day=15
        )
        assert len(result) == 12
        assert all(
            month.amount == 1000.00 or month.amount == 2000.00 or month.amount == 0.0
            for month in result
        )
        assert all(month.amount in [1000.00, 2000.00, 0.0] for month in result)
        assert all(month.transaction_date.year == 2023 for month in result)
        assert all(month.transaction_date.day == 15 for month in result)
        assert all(
            month.status
            in [
                MonthStatusEnum.PAID,
                MonthStatusEnum.CANCELLED,
                MonthStatusEnum.PENDING,
            ]
            for month in result
        )


class TestFinanceMonthsGetMonthStatus:
    @staticmethod
    def test_finance_months_get_month_status_without_status():
        result = get_month_status(
            month=PayloadMonthPersistSchema(amount=1000.00, reference_month=1)
        )
        assert result == MonthStatusEnum.PENDING

    @staticmethod
    def test_finance_months_get_month_status_pending_when_month_is_greater_than_current_month():
        current_datetime = utcnow()
        reference_month = current_datetime.month + 1
        result = get_month_status(
            month=PayloadMonthPersistSchema(
                status=MonthStatusEnum.PAID,
                amount=1000.00,
                reference_month=reference_month,
            )
        )
        assert result == MonthStatusEnum.PENDING

    @staticmethod
    def test_finance_months_get_month_status_paid_when_month_is_less_than_current_month():
        current_datetime = utcnow()
        reference_month = current_datetime.month - 1
        result = get_month_status(
            month=PayloadMonthPersistSchema(
                status=MonthStatusEnum.PAID,
                amount=1000.00,
                reference_month=reference_month,
            )
        )
        assert result == MonthStatusEnum.PAID

    @staticmethod
    def test_finance_months_get_month_status_paid_when_transaction_date_is_greater_than_current_date():
        current_datetime = utcnow()
        reference_month = current_datetime.month + 1
        transaction_date = date(
            current_datetime.year, reference_month, current_datetime.day
        )
        result = get_month_status(
            month=PayloadMonthPersistSchema(
                amount=1000.00,
                reference_month=reference_month,
                transaction_date=transaction_date,
            )
        )
        assert result == MonthStatusEnum.PENDING

    @staticmethod
    def test_finance_months_get_month_status_paid_when_transaction_date_is_less_than_current_date():
        current_datetime = utcnow()
        reference_month = current_datetime.month - 1
        transaction_date = date(
            current_datetime.year, reference_month, current_datetime.day
        )
        result = get_month_status(
            month=PayloadMonthPersistSchema(
                amount=1000.00,
                reference_month=reference_month,
                transaction_date=transaction_date,
            )
        )
        assert result == MonthStatusEnum.PAID


class TestFinanceMonthsGetPaidAt:
    @staticmethod
    def test_finance_months_get_paid_at_status_different_from_paid():
        result = get_paid_at(status=MonthStatusEnum.CANCELLED)
        assert not result

    @staticmethod
    def test_finance_months_get_paid_at_status_paid_when_transaction_date_is_not_none():
        current_datetime = utcnow()
        transaction_date = date(
            current_datetime.year, current_datetime.month, current_datetime.day
        )
        transaction_datetime = datetime(
            year=transaction_date.year,
            month=transaction_date.month,
            day=transaction_date.day,
        )
        result = get_paid_at(
            status=MonthStatusEnum.PAID, transaction_date=transaction_date
        )
        assert result == transaction_datetime

    @staticmethod
    def test_finance_months_get_paid_at_status_paid_when_transaction_date_is_none():
        result = get_paid_at(status=MonthStatusEnum.PAID)
        assert result is not None


class TestFinanceMonthsMergeMonthsByMonth:
    @staticmethod
    def test_finance_months_merge_months_by_reference_month():
        months: list[PayloadMonthPersistSchema] = [
            PayloadMonthPersistSchema(
                amount=1700.00, reference_day=7, reference_month=1
            ),
            PayloadMonthPersistSchema(
                amount=1000.00, reference_day=6, reference_month=2
            ),
            PayloadMonthPersistSchema(
                amount=1500.00, reference_day=9, reference_month=3
            ),
            PayloadMonthPersistSchema(
                amount=1500.00, reference_day=10, reference_month=4
            ),
            PayloadMonthPersistSchema(
                amount=1500.00, reference_day=8, reference_month=5
            ),
            PayloadMonthPersistSchema(
                amount=300.00, reference_day=14, reference_month=5
            ),
            PayloadMonthPersistSchema(
                amount=85.09, reference_day=14, reference_month=5
            ),
            PayloadMonthPersistSchema(
                amount=1500.00, reference_day=5, reference_month=6
            ),
            PayloadMonthPersistSchema(
                amount=300.00, reference_day=12, reference_month=6
            ),
            PayloadMonthPersistSchema(
                amount=450.00, reference_day=16, reference_month=6
            ),
            PayloadMonthPersistSchema(
                amount=450.00, reference_day=16, reference_month=0
            )
        ]
        expected_result: list[PayloadMonthPersistSchema] = [
            PayloadMonthPersistSchema(
                amount=1700.00, reference_day=7, reference_month=1
            ),
            PayloadMonthPersistSchema(
                amount=1000.00, reference_day=6, reference_month=2
            ),
            PayloadMonthPersistSchema(
                amount=1500.00, reference_day=9, reference_month=3
            ),
            PayloadMonthPersistSchema(
                amount=1500.00, reference_day=10, reference_month=4
            ),
            PayloadMonthPersistSchema(
                amount=1885.09, reference_day=14, reference_month=5
            ),
            PayloadMonthPersistSchema(
                amount=2250.00, reference_day=16, reference_month=6
            ),
        ]
        result = merge_months_by_month(months=months)
        assert result == expected_result
