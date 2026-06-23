import pytest

from app.shared.utils.date import (
    generate_description,
    get_month_name,
    get_valid_day,
)


class TestFinanceIncomeGenerateDescriptionBusiness:
    @staticmethod
    def test_generate_description_when_has_description_and_not_item_description():
        month = 1
        source = "Test Source"
        description = "Test Description"
        item_description = None

        result = generate_description(month, source, description, item_description)
        assert result == description

    @staticmethod
    def test_generate_description_when_not_has_description_and_has_item_description():
        month = 1
        source = "Test Source"
        description = None
        item_description = "Test Item Description"
        expected = f"{item_description} | January"

        result = generate_description(month, source, description, item_description)
        assert result == expected

    @staticmethod
    def test_generate_description_when_not_has_description_and_not_has_item_description():
        month = 1
        source = "Test Source"
        description = None
        item_description = None
        expected = f"{source} | January"

        result = generate_description(month, source, description, item_description)
        assert result == expected


class TestFinanceIncomeGetMonthNameBusiness:
    @staticmethod
    def test_get_month_name_when_month_is_1():
        month = 1
        expected = "January"

        result = get_month_name(month)
        assert result == expected

    @staticmethod
    def test_get_month_name_when_month_is_less_than_12():
        month = 13

        with pytest.raises(ValueError, match="Month must be between 1 and 12"):
            get_month_name(month)


class TestFinanceIncomeGetValidDayBusiness:
    @staticmethod
    def test_get_valid_day_when_not_has_day():
        year = 2026
        month = 1
        result = get_valid_day(year, month, None)
        assert result == 3

    @staticmethod
    def test_get_valid_day_when_day_is_bigger_than_31():
        year = 2026
        month = 1
        day = 32
        result = get_valid_day(year, month, day)
        assert result == 31

    @staticmethod
    def test_get_valid_day_when_day_is_less_than_1():
        year = 2026
        month = 1
        day = 0
        result = get_valid_day(year, month, day)
        assert result == 3

    @staticmethod
    def test_get_valid_day_when_day_return_current_day():
        year = 2026
        month = 1
        day = 3
        result = get_valid_day(year, month, day)
        assert result == 3
