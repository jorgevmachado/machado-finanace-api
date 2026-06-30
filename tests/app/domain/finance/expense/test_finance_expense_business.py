from datetime import datetime

from app.domain.finance.expense.business import validate_paid_at, get_status
from app.models import ExpenseStatusEnum, utcnow


class TestFinanceExpenseValidatePaidAtBusiness:
    @staticmethod
    def test_validate_paid_at_business_status_paid_not_paid_at():
        status = ExpenseStatusEnum.PAID
        paid_at = None
        result = validate_paid_at(status, paid_at)
        assert result is not None

    @staticmethod
    def test_validate_paid_at_business_status_paid_and_paid_at():
        status = ExpenseStatusEnum.PAID
        paid_at = utcnow()
        result = validate_paid_at(status, paid_at)
        assert result == paid_at

    @staticmethod
    def test_validate_paid_at_business_status_not_paid_and_paid_at():
        status = ExpenseStatusEnum.PENDING
        paid_at = utcnow()
        result = validate_paid_at(status, paid_at)
        assert result is None

class TestFinanceExpenseGetStatus:
    @staticmethod
    def test_get_status_reference_month_pending():
        current_date = utcnow()
        reference_month = current_date.month + 1
        result = get_status(
            status=ExpenseStatusEnum.PENDING,
            reference_month=reference_month
        )
        result == ExpenseStatusEnum.PENDING

    @staticmethod
    def test_get_status_reference_month_paid():
        current_date = utcnow()
        reference_month = current_date.month
        result = get_status(
            status=ExpenseStatusEnum.PENDING,
            reference_month=reference_month
        )
        result == ExpenseStatusEnum.PAID

    @staticmethod
    def test_get_status_paid_at_pending():
        current_date = utcnow()
        reference_month = current_date.month + 1
        paid_at = datetime(month=reference_month, year=current_date.year, day=current_date.day)
        result = get_status(
            status=ExpenseStatusEnum.PENDING,
            paid_at=paid_at
        )
        result == ExpenseStatusEnum.PENDING

    @staticmethod
    def test_get_status_paid_at_paid():
        current_date = utcnow()
        paid_at = current_date
        result = get_status(status=ExpenseStatusEnum.PENDING, paid_at=paid_at)
        result == ExpenseStatusEnum.PAID

    @staticmethod
    def test_get_status_payload():
        result = get_status(status=ExpenseStatusEnum.CANCELLED)
        result == ExpenseStatusEnum.CANCELLED