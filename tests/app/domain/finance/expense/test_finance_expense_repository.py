from unittest.mock import MagicMock, Mock, AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi_pagination import LimitOffsetParams

from app.core.pagination import CustomLimitOffsetPage
from app.domain.finance.expense.repository import ExpenseRepository
from app.models import Expense, utcnow, ExpenseMonth, MonthStatusEnum
from app.shared.schemas import FilterPage


@pytest.fixture()
def expense():
    expense = MagicMock(spec=Expense)
    expense.id = uuid4()
    expense.months = []
    expense.payee = "Test Expense"
    expense.category_id = uuid4()
    expense.allocation_id = uuid4()
    expense.payee_code = "test_expense"
    expense.description = "Test Expense Description"
    expense.created_at = utcnow()
    expense.updated_at = None
    expense.deleted_at = None

    for i in range(1, 13):
        expense_month_2025 = MagicMock(spec=ExpenseMonth)
        expense_month_2025.id = uuid4()
        expense_month_2025.amount = 100
        expense_month_2025.status = MonthStatusEnum.PAID
        expense_month_2025.expense_id = expense.id
        expense_month_2025.reference_year = 2025
        expense_month_2025.reference_month = i
        expense_month_2025.paid_at = utcnow()
        expense_month_2025.created_at = utcnow()
        expense_month_2025.updated_at = None
        expense_month_2025.deleted_at = None
        expense.months.append(expense_month_2025)

        expense_month_2026 = MagicMock(spec=ExpenseMonth)
        expense_month_2026.id = uuid4()
        expense_month_2026.amount = 400
        expense_month_2026.status = MonthStatusEnum.PENDING
        expense_month_2026.expense_id = expense.id
        expense_month_2026.reference_year = 2026
        expense_month_2026.reference_month = i
        expense_month_2026.paid_at = None
        expense_month_2026.created_at = utcnow()
        expense_month_2026.updated_at = None
        expense_month_2026.deleted_at = None
        expense.months.append(expense_month_2026)
    
    return expense

class TestFinanceIncomeRepositoryListAll:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_repository_list_all_with_reference_year_none(
        expense,
    ):
        expected_items = [expense]
        scalars_result = Mock()
        scalars_result.all.return_value = expected_items

        mock_session = AsyncMock()
        mock_session.scalars = AsyncMock(return_value=scalars_result)

        repository = ExpenseRepository(session=mock_session)

        with patch("app.core.repository.base.is_paginate", return_value=False):
            result = await repository.list_all()

        assert result[0] == expense
        assert len(result[0].months) == 24

        mock_session.scalars.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_repository_list_all_with_reference_year_and_list(
        expense,
    ):
        page_filter = FilterPage()
        expected_items = [expense]
        scalars_result = Mock()
        scalars_result.all.return_value = expected_items

        mock_session = AsyncMock()
        mock_session.scalars = AsyncMock(return_value=scalars_result)

        repository = ExpenseRepository(session=mock_session)

        with patch("app.core.repository.base.is_paginate", return_value=False):
            result = await repository.list_all(
                page_filter=FilterPage.build(
                    page_filter=page_filter, reference_year=2026
                )
            )

        assert result[0] == expense
        assert len(result[0].months) == 12

        mock_session.scalars.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_repository_list_all_with_reference_year_and_list_with_incomes_months_empty(
        expense,
    ):
        expected_items = [expense]
        scalars_result = Mock()
        scalars_result.all.return_value = expected_items

        mock_session = AsyncMock()
        mock_session.scalars = AsyncMock(return_value=scalars_result)
        page_filter = FilterPage()

        repository = ExpenseRepository(session=mock_session)

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
    async def test_finance_expense_repository_list_all_with_reference_year_and_paginate(
        expense,
    ):
        params = LimitOffsetParams(limit=50, offset=0)
        expected_page = CustomLimitOffsetPage.create(
            items=[expense],
            total=1,
            params=params,
        )            
        mock_session = AsyncMock()        
        repository = ExpenseRepository(session=mock_session)
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
    async def test_finance_expense_repository_find_by_with_reference_year_none(expense):
        expected_entity = expense
        mock_session = AsyncMock()
        mock_session.scalar = AsyncMock(return_value=expected_entity)

        repository = ExpenseRepository(session=mock_session)
        result = await repository.find_by(id=expense.id)

        assert result == expected_entity
        mock_session.scalar.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_repository_find_by_with_reference_year_return_none(expense):
        expected_entity = expense
        mock_session = AsyncMock()
        mock_session.scalar = AsyncMock(return_value=expected_entity)

        repository = ExpenseRepository(session=mock_session)
        result = await repository.find_by(id=expense.id, reference_year=2025)

        assert result == expected_entity
        if result is not None:
            assert len(result.months) == 12

        mock_session.scalar.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_repository_find_by_with_reference_year(expense):
        mock_session = AsyncMock()
        mock_session.scalar = AsyncMock(return_value=None)

        repository = ExpenseRepository(session=mock_session)
        result = await repository.find_by(id=expense.id, reference_year=2025)

        assert result is None
        mock_session.scalar.assert_awaited_once()