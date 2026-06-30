from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.domain.finance.repository import FinanceRepository


@pytest.fixture
def finance_repository() -> tuple[FinanceRepository, AsyncMock]:
    session = AsyncMock()
    return FinanceRepository(session=session), session


class TestFinanceRepository:
    @staticmethod
    @pytest.mark.asyncio
    async def test_find_by_finance_year_returns_scalar_result(
        finance_repository: tuple[FinanceRepository, AsyncMock],
    ):
        repository, session = finance_repository
        finance = SimpleNamespace(id=uuid4())
        session.scalar.side_effect = [1, 1, 1, finance]

        result = await repository.find_by_finance_year(
            finance_id=finance.id,
            reference_year=2026,
        )

        assert result == finance
        assert session.scalar.await_count == 4

    @staticmethod
    @pytest.mark.asyncio
    async def test_find_by_finance_year_builds_query_with_year_filters(
        finance_repository: tuple[FinanceRepository, AsyncMock],
    ):
        repository, session = finance_repository
        finance_id = uuid4()
        session.scalar.side_effect = [1, 0, 0, None]

        await repository.find_by_finance_year(
            finance_id=finance_id,
            reference_year=2026,
        )

        query = session.scalar.await_args_list[-1].args[0]
        assert len(query._with_options) == 5

        options_text = " ".join(str(option) for option in query._with_options)
        assert "LoaderCriteriaOption" in options_text

    @staticmethod
    @pytest.mark.asyncio
    async def test_find_by_finance_year_returns_none_when_no_yearly_data(
        finance_repository: tuple[FinanceRepository, AsyncMock],
    ):
        repository, session = finance_repository
        finance_id = uuid4()
        session.scalar.side_effect = [0, 0, 0]

        result = await repository.find_by_finance_year(
            finance_id=finance_id,
            reference_year=2025,
        )

        assert result is None
        assert session.scalar.await_count == 3
