from datetime import date
from unittest.mock import MagicMock, Mock, AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi_pagination import LimitOffsetParams

from app.core.pagination import CustomLimitOffsetPage
from app.domain.finance.income.repository import IncomeRepository
from app.models import Income, utcnow, IncomeMonth
from app.shared.schemas import FilterPage


@pytest.fixture()
def income():
    income = MagicMock(spec=Income)
    income.id = uuid4()
    income.months = []
    income.source = "Test Income"
    income.account_id = uuid4()
    income.source_code = "test_income"
    income.description = "Test Income Description"
    income.created_at = utcnow()
    income.updated_at = None
    income.deleted_at = None

    for i in range(1, 13):
        income_month_2025 = MagicMock(spec=IncomeMonth)
        income_month_2025.id = uuid4()
        income_month_2025.amount = 100
        income_month_2025.income_id = income.id
        income_month_2025.reference_year = 2025
        income_month_2025.reference_month = i
        income_month_2025.received_at = date(year=2025, month=i, day=1)
        income_month_2025.created_at = utcnow()
        income_month_2025.updated_at = None
        income_month_2025.deleted_at = None
        income.months.append(income_month_2025)

        income_month_2026 = MagicMock(spec=IncomeMonth)
        income_month_2026.id = uuid4()
        income_month_2026.amount = 400
        income_month_2026.income_id = income.id
        income_month_2026.reference_year = 2026
        income_month_2026.reference_month = i
        income_month_2026.received_at = date(year=2026, month=i, day=1)
        income_month_2026.created_at = utcnow()
        income_month_2026.updated_at = None
        income_month_2026.deleted_at = None
        income.months.append(income_month_2026)
    
    return income

class TestFinanceIncomeRepositoryListAll:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_repository_list_all_with_reference_year_none(
        income,
    ):
        expected_items = [income]
        scalars_result = Mock()
        scalars_result.all.return_value = expected_items

        mock_session = AsyncMock()
        mock_session.scalars = AsyncMock(return_value=scalars_result)

        repository = IncomeRepository(session=mock_session)

        with patch("app.core.repository.base.is_paginate", return_value=False):
            result = await repository.list_all()

        assert result[0] == income
        assert len(result[0].months) == 24

        mock_session.scalars.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_repository_list_all_with_reference_year_and_list(
        income,
    ):
        page_filter = FilterPage()
        expected_items = [income]
        scalars_result = Mock()
        scalars_result.all.return_value = expected_items

        mock_session = AsyncMock()
        mock_session.scalars = AsyncMock(return_value=scalars_result)

        repository = IncomeRepository(session=mock_session)

        with patch("app.core.repository.base.is_paginate", return_value=False):
            result = await repository.list_all(
                page_filter=FilterPage.build(
                    page_filter=page_filter, reference_year=2026
                )
            )

        assert result[0] == income
        assert len(result[0].months) == 12

        mock_session.scalars.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_repository_list_all_with_reference_year_and_list_with_incomes_months_empty(
        income,
    ):
        expected_items = [income]
        scalars_result = Mock()
        scalars_result.all.return_value = expected_items

        mock_session = AsyncMock()
        mock_session.scalars = AsyncMock(return_value=scalars_result)
        page_filter = FilterPage()

        repository = IncomeRepository(session=mock_session)

        with patch("app.core.repository.base.is_paginate", return_value=False):
            result = await repository.list_all(
                page_filter=FilterPage.build(
                    page_filter=page_filter, reference_year=2000
                )
            )

        assert len(result) == 1
        result_months = result[0].months
        assert len(result_months) == 0
        mock_session.scalars.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_repository_list_all_with_reference_year_and_paginate(
        income,
    ):
        params = LimitOffsetParams(limit=50, offset=0)
        expected_page = CustomLimitOffsetPage.create(
            items=[income],
            total=1,
            params=params,
        )            
        mock_session = AsyncMock()        
        repository = IncomeRepository(session=mock_session)
        page_filter = FilterPage(offset=0, limit=50)
        
        with (
            patch("app.core.repository.base.is_paginate", return_value=True),
            patch(
                "app.core.repository.base.get_limit_offset_params",
                return_value=params,
            ),
            patch(
                "app.core.repository.base.paginate", new_callable=AsyncMock
            ) as paginate_mock,
        ):
            paginate_mock.return_value = expected_page
            result = await repository.list_all(
                page_filter=FilterPage.build(
                    page_filter=page_filter, reference_year=2025
                )
            )

        assert result is expected_page
        result_items = result.items
        result_items_months = result_items[0].months
        assert len(result_items_months) == 12

class TestFinanceIncomeRepositoryFindBy:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_repository_find_by_with_reference_year_none(income):
        expected_entity = income
        mock_session = AsyncMock()
        mock_session.scalar = AsyncMock(return_value=expected_entity)

        repository = IncomeRepository(session=mock_session)
        result = await repository.find_by(id=income.id)

        assert result == expected_entity
        mock_session.scalar.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_repository_find_by_with_reference_return_none(income):
        expected_entity = income
        mock_session = AsyncMock()
        mock_session.scalar = AsyncMock(return_value=expected_entity)

        repository = IncomeRepository(session=mock_session)
        result = await repository.find_by(id=income.id, reference_year=2025)

        assert result == expected_entity
        if result is not None:
            assert len(result.months) == 12

        mock_session.scalar.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_repository_find_by_with_reference_year(income):
        mock_session = AsyncMock()
        mock_session.scalar = AsyncMock(return_value=None)

        repository = IncomeRepository(session=mock_session)
        result = await repository.find_by(id=income.id, reference_year=2025)

        assert result is None
        mock_session.scalar.assert_awaited_once()