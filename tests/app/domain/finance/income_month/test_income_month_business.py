from __future__ import annotations

from datetime import date

from app.domain.finance.income_month.business import validate_received_at

class TestIncomeBusinessValidateReceivedAt:
    @staticmethod
    def test_income_business_validate_received_at():

        valid_date = date(2026, 7, 20)
        result = validate_received_at(
            year=2026,
            day=20,
            month=7,
            received_at=valid_date
        )
        assert result == valid_date

    @staticmethod
    def test_income_business_validate_received_at_with_none():
        result = validate_received_at(
            year=2026,
            day=20,
            month=7,
            received_at=None
        )
        assert result == date(2026, 7, 20)