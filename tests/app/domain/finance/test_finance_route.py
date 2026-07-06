from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domain.finance.route import (
    onboarding,
    finance_service,
)
from app.domain.finance.service import FinanceService


def test_finance_builds_service() -> None:
    service = finance_service(AsyncMock())
    assert isinstance(service, FinanceService)


@pytest.mark.asyncio
async def test_finance_route_onboarding() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(id="finance-id")
    service.onboard.return_value = expected
    current_user = SimpleNamespace(id="user-id", username="Finance User")

    result = await onboarding(service=service, current_user=current_user)

    assert result is expected
    service.onboard.assert_awaited_once_with(current_user=current_user)


@pytest.mark.asyncio
async def test_finance_route_persist_success() -> None:
    from app.domain.finance.route import persist

    service = AsyncMock()
    expected = SimpleNamespace(
        incomes=1,
        accounts=1,
        expenses=1,
        categories=1,
        allocations=1,
    )
    service.persist.return_value = expected
    finance = SimpleNamespace(id="finance-id")
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=finance
    )
    payloads = [
        SimpleNamespace(
            name="Test Account",
            type="BANK",
            initial_balance=1000,
        )
    ]

    result = await persist(
        service=service, current_user=current_user, payloads=payloads
    )

    assert result is expected
    service.persist.assert_awaited_once_with(finance=finance, payloads=payloads)
