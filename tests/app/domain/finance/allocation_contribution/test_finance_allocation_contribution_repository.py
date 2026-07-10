from datetime import date
from unittest.mock import MagicMock, Mock, AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi_pagination import LimitOffsetParams

from app.core.pagination import CustomLimitOffsetPage
from app.domain.finance.allocation_contribution.repository import AllocationContributionRepository
from app.models import (
    utcnow,
    AllocationContribution,
    AllocationContributionMonth,
)
from app.shared.schemas import FilterPage

@pytest.fixture
def allocation_contribution():
    allocation_contribution = MagicMock(spec=AllocationContribution)
    allocation_contribution.id = uuid4()
    allocation_contribution.months = []
    allocation_contribution.description = "Some Description"
    allocation_contribution.contribution_name = "Some Contribution Name"
    allocation_contribution.contribution_name_code = "some_contribution_name"
    allocation_contribution.allocation_id = uuid4()
    allocation_contribution.created_at = utcnow()
    allocation_contribution.updated_at = None
    allocation_contribution.deleted_at = None

    for i in range(1, 13):
        allocation_contribution_month_2025 = MagicMock(spec=AllocationContributionMonth)
        allocation_contribution_month_2025.id = uuid4()
        allocation_contribution_month_2025.amount = 100
        allocation_contribution_month_2025.allocation_contribution_id = allocation_contribution.id
        allocation_contribution_month_2025.reference_year = 2025
        allocation_contribution_month_2025.reference_month = i
        allocation_contribution_month_2025.received_at = date(year=2025, month=i, day=1)
        allocation_contribution_month_2025.created_at = utcnow()
        allocation_contribution_month_2025.updated_at = None
        allocation_contribution_month_2025.deleted_at = None
        allocation_contribution.months.append(allocation_contribution_month_2025)

        allocation_contribution_month_2026 = MagicMock(spec=AllocationContributionMonth)
        allocation_contribution_month_2026.id = uuid4()
        allocation_contribution_month_2026.amount = 400
        allocation_contribution_month_2026.allocation_contribution_id = allocation_contribution.id
        allocation_contribution_month_2026.reference_year = 2026
        allocation_contribution_month_2026.reference_month = i
        allocation_contribution_month_2026.paid_at = None
        allocation_contribution_month_2026.created_at = utcnow()
        allocation_contribution_month_2026.updated_at = None
        allocation_contribution_month_2026.deleted_at = None
        allocation_contribution.months.append(allocation_contribution_month_2026)

    return allocation_contribution


class TestFinanceAllocationContributionRepositoryListAll:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_contribution_repository_list_all_with_reference_year_none(
        allocation_contribution,
    ):
        expected_items = [allocation_contribution]
        scalars_result = Mock()
        scalars_result.all.return_value = expected_items

        mock_session = AsyncMock()
        mock_session.scalars = AsyncMock(return_value=scalars_result)

        repository = AllocationContributionRepository(session=mock_session)

        with patch("app.core.repository.base.is_paginate", return_value=False):
            result = await repository.list_all()

        assert result[0] == allocation_contribution
        assert len(result[0].months) == 24

        mock_session.scalars.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_contribution_repository_list_all_with_reference_year_and_list(
        allocation_contribution,
    ):
        page_filter = FilterPage()
        expected_items = [allocation_contribution]
        scalars_result = Mock()
        scalars_result.all.return_value = expected_items

        mock_session = AsyncMock()
        mock_session.scalars = AsyncMock(return_value=scalars_result)

        repository = AllocationContributionRepository(session=mock_session)

        with patch("app.core.repository.base.is_paginate", return_value=False):
            result = await repository.list_all(
                page_filter=FilterPage.build(
                    page_filter=page_filter, reference_year=2026
                )
            )

        assert result[0] == allocation_contribution
        assert len(result[0].months) == 12

        mock_session.scalars.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_contribution_repository_list_all_with_reference_year_and_list_with_incomes_months_empty(
        allocation_contribution,
    ):
        expected_items = [allocation_contribution]
        scalars_result = Mock()
        scalars_result.all.return_value = expected_items

        mock_session = AsyncMock()
        mock_session.scalars = AsyncMock(return_value=scalars_result)
        page_filter = FilterPage()

        repository = AllocationContributionRepository(session=mock_session)

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
    async def test_finance_allocation_contribution_repository_list_all_with_reference_year_and_paginate(
        allocation_contribution,
    ):
        params = LimitOffsetParams(limit=50, offset=0)
        expected_page = CustomLimitOffsetPage.create(
            items=[allocation_contribution],
            total=1,
            params=params,
        )            
        mock_session = AsyncMock()        
        repository = AllocationContributionRepository(session=mock_session)
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

class TestFinanceAllocationContributionRepositoryFindBy:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_contribution_repository_find_by_with_reference_year_none(allocation_contribution):
        expected_entity = allocation_contribution
        mock_session = AsyncMock()
        mock_session.scalar = AsyncMock(return_value=expected_entity)

        repository = AllocationContributionRepository(session=mock_session)
        result = await repository.find_by(id=allocation_contribution.id)

        assert result == expected_entity
        mock_session.scalar.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_contribution_repository_find_by_with_reference_year_return_none(allocation_contribution):
        expected_entity = allocation_contribution
        mock_session = AsyncMock()
        mock_session.scalar = AsyncMock(return_value=expected_entity)

        repository = AllocationContributionRepository(session=mock_session)
        result = await repository.find_by(id=allocation_contribution.id, reference_year=2025)

        assert result == expected_entity
        if result is not None:
            assert len(result.months) == 12

        mock_session.scalar.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_contribution_repository_find_by_with_reference_year(allocation_contribution):
        mock_session = AsyncMock()
        mock_session.scalar = AsyncMock(return_value=None)

        repository = AllocationContributionRepository(session=mock_session)
        result = await repository.find_by(id=allocation_contribution.id, reference_year=2025)

        assert result is None
        mock_session.scalar.assert_awaited_once()