from app.domain.finance.expense.business import validate_paid_at
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
