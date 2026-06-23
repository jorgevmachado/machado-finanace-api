from app.domain.finance.transaction.business import validate_paid_at
from app.models import TransactionStatusEnum, utcnow


class TestFinanceTransactionValidatePaidAtBusiness:
    @staticmethod
    def test_validate_paid_at_business_status_paid_not_paid_at():
        status = TransactionStatusEnum.PAID
        paid_at = None
        result = validate_paid_at(status, paid_at)
        assert result is not None

    @staticmethod
    def test_validate_paid_at_business_status_paid_and_paid_at():
        status = TransactionStatusEnum.PAID
        paid_at = utcnow()
        result = validate_paid_at(status, paid_at)
        assert result == paid_at

    @staticmethod
    def test_validate_paid_at_business_status_not_paid_and_paid_at():
        status = TransactionStatusEnum.PENDING
        paid_at = utcnow()
        result = validate_paid_at(status, paid_at)
        assert result is None