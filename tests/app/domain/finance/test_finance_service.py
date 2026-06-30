from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4


import pytest
from fastapi import HTTPException

from app.domain.finance.service import FinanceService
from app.models import AccountTypeEnum, AllocationTypeEnum

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


class TestFinanceFindByUserService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_find_by_user_service_no_has_finance(
        finance_repository_mock: AsyncMock,
    ):
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=None
        )

        service = FinanceService(repository=finance_repository_mock)

        with pytest.raises(HTTPException) as exc_info:
            await service.find_by_user(current_user=current_user)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"User {current_user.username} must be onboarded first"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_find_by_user_service_successfully(
        finance_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=finance
        )

        service = FinanceService(repository=finance_repository_mock)
        service.find_one = AsyncMock(return_value=finance)

        result = await service.find_by_user(current_user=current_user)

        assert result == finance


class TestFinanceCreateService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_create_orchestrates_account_income_and_allocations(
        finance_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(
            id=uuid4(), user=SimpleNamespace(username="Finance User")
        )
        payload = SimpleNamespace(
            name="Personal",
            type=AccountTypeEnum.BANK,
            initialize_balance=100,
            reference_day=5,
            reference_year=2026,
            incomes=[SimpleNamespace()],
            allocations=[SimpleNamespace()],
        )
        account = SimpleNamespace(id=uuid4())

        service = FinanceService(repository=finance_repository_mock)
        service.account_service.persist = AsyncMock(return_value=account)
        service.income_service.create_by_account = AsyncMock()
        service.create_allocations_by_account = AsyncMock()
        service.find_one = AsyncMock(return_value=finance)

        result = await service.create(finance=finance, payloads=[payload])

        assert result == finance
        service.account_service.persist.assert_awaited_once()
        service.income_service.create_by_account.assert_awaited_once_with(
            finance=finance,
            account=account,
            reference_day=5,
            reference_year=2026,
            payload_incomes=payload.incomes,
        )
        service.create_allocations_by_account.assert_awaited_once_with(
            finance=finance,
            account=account,
            reference_day=5,
            reference_year=2026,
            payload_allocations=payload.allocations,
        )
        service.find_one.assert_awaited_once_with(
            param=str(finance.id), user_request=finance.user.username
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_create_allocations_by_account_calls_expense_and_contribution_services(
        finance_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())
        payload_allocation = SimpleNamespace(
            name="Residencial",
            type=AllocationTypeEnum.HOUSE,
            description="Despesas",
            categories=[SimpleNamespace(name="Internet")],
            contributions=[SimpleNamespace(contributor_name="Jorge")],
        )

        service = FinanceService(repository=finance_repository_mock)
        service.allocation_service.persist = AsyncMock(return_value=allocation)
        service.expense_service.create_by_account = AsyncMock(return_value=[])
        service.allocation_contribution_service.create_by_account = AsyncMock(
            return_value=[]
        )

        await service.create_allocations_by_account(
            finance=finance,
            account=account,
            reference_day=5,
            reference_year=2026,
            payload_allocations=[payload_allocation],
        )

        service.allocation_service.persist.assert_awaited_once()
        service.expense_service.create_by_account.assert_awaited_once_with(
            finance=finance,
            account=account,
            allocation=allocation,
            reference_day=5,
            reference_year=2026,
            payload_categories=payload_allocation.categories,
        )
        service.allocation_contribution_service.create_by_account.assert_awaited_once_with(
            finance=finance,
            account=account,
            allocation=allocation,
            reference_year=2026,
            payload_allocation_contributions=payload_allocation.contributions,
        )