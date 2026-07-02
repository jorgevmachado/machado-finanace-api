from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domain.finance.repository import FinanceRepository
from app.models import Finance


@pytest.fixture
def finance_repository() -> tuple[FinanceRepository, AsyncMock]:
    session = AsyncMock()
    return FinanceRepository(session=session), session


class TestFinanceRepository:
    @staticmethod
    def test_finance_repository_builds_correctly(finance_repository):
        repository, session = finance_repository
        assert isinstance(repository, FinanceRepository)
        assert repository.session is session
        assert repository.model.__name__ == "Finance"

    @staticmethod
    @pytest.mark.asyncio
    async def test_find_by_finance_year_returns_none_when_no_data(
        finance_repository,
    ):
        """Test find_by_finance_year returns None when yearly_total is 0."""
        repository, session = finance_repository
        session.scalar = AsyncMock(return_value=None)

        finance_id = uuid4()

        result = await repository.find_by_finance_year(
            finance_id=finance_id,
            reference_year=2026,
        )

        assert result is None
        assert session.scalar.call_count == 3

    @staticmethod
    @pytest.mark.asyncio
    async def test_find_by_finance_year_with_income_months(finance_repository):
        """Test find_by_finance_year returns Finance when IncomeMonth exists."""
        repository, session = finance_repository
        mock_finance = MagicMock(spec=Finance)
        mock_finance.id = uuid4()

        session.scalar = AsyncMock(
            side_effect=[1, 0, 0, mock_finance]
        )

        finance_id = uuid4()

        result = await repository.find_by_finance_year(
            finance_id=finance_id,
            reference_year=2026,
        )

        assert result == mock_finance
        assert session.scalar.call_count == 4

    @staticmethod
    @pytest.mark.asyncio
    async def test_find_by_finance_year_with_expense_months(finance_repository):
        """Test find_by_finance_year returns Finance when ExpenseMonth exists."""
        repository, session = finance_repository
        mock_finance = MagicMock(spec=Finance)

        session.scalar = AsyncMock(side_effect=[0, 2, 0, mock_finance])

        finance_id = uuid4()

        result = await repository.find_by_finance_year(
            finance_id=finance_id,
            reference_year=2026,
        )

        assert result == mock_finance

    @staticmethod
    @pytest.mark.asyncio
    async def test_find_by_finance_year_with_contributions(finance_repository):
        """Test find_by_finance_year returns Finance when AllocationContribution exists."""
        repository, session = finance_repository
        mock_finance = MagicMock(spec=Finance)

        session.scalar = AsyncMock(side_effect=[0, 0, 3, mock_finance])

        finance_id = uuid4()

        result = await repository.find_by_finance_year(
            finance_id=finance_id,
            reference_year=2026,
        )

        assert result == mock_finance

    @staticmethod
    @pytest.mark.asyncio
    async def test_find_by_finance_year_with_all_data_types(finance_repository):
        """Test find_by_finance_year returns Finance with all data types."""
        repository, session = finance_repository
        mock_finance = MagicMock(spec=Finance)

        session.scalar = AsyncMock(side_effect=[5, 3, 2, mock_finance])

        finance_id = uuid4()

        result = await repository.find_by_finance_year(
            finance_id=finance_id,
            reference_year=2026,
        )

        assert result == mock_finance

    @staticmethod
    @pytest.mark.asyncio
    async def test_find_by_finance_year_returns_finance_not_found(
        finance_repository,
    ):
        """Test find_by_finance_year returns None when Finance not found."""
        repository, session = finance_repository

        session.scalar = AsyncMock(side_effect=[1, 0, 0, None])

        finance_id = uuid4()

        result = await repository.find_by_finance_year(
            finance_id=finance_id,
            reference_year=2026,
        )

        assert result is None

    @staticmethod
    @pytest.mark.asyncio
    async def test_find_by_finance_year_with_deleted_false(finance_repository):
        """Test find_by_finance_year applies deleted_at.is_(None) predicates."""
        repository, session = finance_repository
        mock_finance = MagicMock(spec=Finance)

        session.scalar = AsyncMock(side_effect=[1, 0, 0, mock_finance])

        finance_id = uuid4()

        result = await repository.find_by_finance_year(
            finance_id=finance_id,
            reference_year=2026,
            with_deleted=False,
        )

        assert result == mock_finance

    @staticmethod
    @pytest.mark.asyncio
    async def test_find_by_finance_year_with_deleted_true(finance_repository):
        """Test find_by_finance_year includes deleted items when with_deleted=True."""
        repository, session = finance_repository
        mock_finance = MagicMock(spec=Finance)

        session.scalar = AsyncMock(side_effect=[1, 0, 0, mock_finance])

        finance_id = uuid4()

        result = await repository.find_by_finance_year(
            finance_id=finance_id,
            reference_year=2026,
            with_deleted=True,
        )

        assert result == mock_finance


