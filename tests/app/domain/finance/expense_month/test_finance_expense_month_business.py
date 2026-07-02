from datetime import datetime, timezone


from app.models import MonthStatusEnum
from app.domain.finance.expense_month.business import validate_paid_at, get_status


class TestValidatePaidAt:
    def test_validate_paid_at_paid_without_date_returns_utcnow(self):
        result = validate_paid_at(MonthStatusEnum.PAID, None)
        assert result is not None
        assert isinstance(result, datetime)

    def test_validate_paid_at_paid_with_date_returns_date(self):
        test_date = datetime(2026, 7, 1, tzinfo=timezone.utc)
        result = validate_paid_at(MonthStatusEnum.PAID, test_date)
        assert result == test_date

    def test_validate_paid_at_pending_with_date_returns_none(self):
        test_date = datetime(2026, 7, 1, tzinfo=timezone.utc)
        result = validate_paid_at(MonthStatusEnum.PENDING, test_date)
        assert result is None

    def test_validate_paid_at_pending_without_date_returns_none(self):
        result = validate_paid_at(MonthStatusEnum.PENDING, None)
        assert result is None

    def test_validate_paid_at_cancelled_with_date_returns_none(self):
        test_date = datetime(2026, 7, 1, tzinfo=timezone.utc)
        result = validate_paid_at(MonthStatusEnum.CANCELLED, test_date)
        assert result is None


class TestGetStatus:
    def test_get_status_default_returns_pending(self):
        result = get_status()
        assert result == MonthStatusEnum.PENDING

    def test_get_status_explicit_paid_returns_paid(self):
        result = get_status(status=MonthStatusEnum.PAID)
        assert result == MonthStatusEnum.PAID

    def test_get_status_reference_month_past_returns_paid(self):
        result = get_status(
            status=MonthStatusEnum.PENDING,
            reference_month=5,
        )
        assert result == MonthStatusEnum.PAID

    def test_get_status_reference_month_future_returns_pending(self):
        result = get_status(
            status=MonthStatusEnum.PENDING,
            reference_month=12,
        )
        assert result == MonthStatusEnum.PENDING

    def test_get_status_paid_at_past_returns_paid(self):
        past_date = datetime(2026, 1, 1, tzinfo=timezone.utc)
        result = get_status(
            status=MonthStatusEnum.PENDING,
            paid_at=past_date,
        )
        assert result == MonthStatusEnum.PAID

    def test_get_status_paid_at_future_returns_pending(self):
        future_date = datetime(2099, 12, 31, tzinfo=timezone.utc)
        result = get_status(
            status=MonthStatusEnum.PENDING,
            paid_at=future_date,
        )
        assert result == MonthStatusEnum.PENDING

    def test_get_status_paid_at_without_tz_returns_paid(self):
        past_date = datetime(2026, 1, 1)
        result = get_status(
            status=MonthStatusEnum.PENDING,
            paid_at=past_date,
        )
        assert result == MonthStatusEnum.PAID

    def test_get_status_explicit_paid_ignores_reference_month(self):
        result = get_status(
            status=MonthStatusEnum.PAID,
            reference_month=12,
        )
        assert result == MonthStatusEnum.PAID

    def test_get_status_cancelled_returns_cancelled(self):
        result = get_status(status=MonthStatusEnum.CANCELLED)
        assert result == MonthStatusEnum.CANCELLED
