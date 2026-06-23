from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domain.finance.route import onboarding, finance_service, find_by_user
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
async def test_finance_route_find_by_user() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(id="finance-id")
    service.find_by_user.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=expected
    )

    result = await find_by_user(service=service, current_user=current_user)

    assert result is expected
    service.find_by_user.assert_awaited_once_with(current_user=current_user)
