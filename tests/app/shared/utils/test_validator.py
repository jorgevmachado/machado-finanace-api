from http import HTTPStatus

import pytest
from fastapi import HTTPException

from app.models import utcnow
from app.shared.utils.validator import validate_year, validate_month


class TestUtilsValidateYearValidator:
    @staticmethod
    def test_utils_validate_year_with_none_year():
        with pytest.raises(HTTPException) as exc_info:
            validate_year(None)
        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST

    @staticmethod
    def test_utils_validate_year_with_greater_than_current_year():
        current_year = utcnow().year + 1
        with pytest.raises(HTTPException) as exc_info:
            validate_year(current_year)
        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST

    @staticmethod
    def test_utils_validate_year_with_valid_year():
        current_year = utcnow().year - 1
        result = validate_year(current_year)
        assert result == current_year


class TestUtilsValidateMonthValidator:
    @staticmethod
    def test_utils_validate_month_with_month_less_than_1():
        month = 0
        with pytest.raises(HTTPException) as exc_info:
            validate_month(month)
        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail == f"Reference month {month} must be between 1 and 12"
        )

    @staticmethod
    def test_utils_validate_month_with_month_greater_than_12():
        month = 13
        with pytest.raises(HTTPException) as exc_info:
            validate_month(month)
        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail == f"Reference month {month} must be between 1 and 12"
        )

    @staticmethod
    def test_utils_validate_month_with_valid_month():
        month = 7
        result = validate_month(month)
        assert result == month
