from __future__ import annotations

from datetime import date

from app.domain.finance.income.business import get_received_at


class TestIncomeBusiness:
    @staticmethod
    def test_get_received_at_returns_correct_date():
        result = get_received_at(year=2026, month=1, day=15)
        assert result == date(2026, 1, 15)

    @staticmethod
    def test_get_received_at_with_different_dates():
        result = get_received_at(year=2025, month=12, day=31)
        assert result == date(2025, 12, 31)
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 31

    @staticmethod
    def test_get_received_at_february():
        result = get_received_at(year=2024, month=2, day=29)
        assert result == date(2024, 2, 29)
