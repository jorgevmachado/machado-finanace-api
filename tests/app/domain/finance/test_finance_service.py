from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4


import pytest
from fastapi import HTTPException

from app.domain.finance.service import FinanceService


@pytest.fixture
def finance_repository_mock() -> AsyncMock:
    return AsyncMock()


class TestFinanceServiceFromSession:
    @staticmethod
    @pytest.mark.asyncio
    async def test_from_session_builds_service() -> None:
        service = FinanceService.from_session(AsyncMock())
        assert isinstance(service, FinanceService)


class TestFinanceOnboardingService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_onboarding_service_has_onboarding(
        finance_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=finance.id)
        )

        service = FinanceService(repository=finance_repository_mock)

        with pytest.raises(HTTPException) as exc_info:
            await service.onboard(current_user=current_user)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail == f"User {current_user.username} already onboarded"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_onboarding_service_success_onboarding(
        finance_repository_mock: AsyncMock,
    ):
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=None
        )
        finance = SimpleNamespace(id=uuid4(), user_id=current_user.id)
        finance_repository_mock.create.return_value = finance
        finance_repository_mock.save.return_value = SimpleNamespace(
            id=finance.id, user_id=current_user.id
        )

        service = FinanceService(repository=finance_repository_mock)
        result = await service.onboard(current_user=current_user)
        assert result == finance
