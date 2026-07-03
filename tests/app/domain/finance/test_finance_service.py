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

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_find_by_user_service_with_year_uses_repository_method(
        finance_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(
            id=uuid4(),
            incomes=[SimpleNamespace(id=uuid4())],
            expenses=[],
            allocation_contributions=[],
            allocations=[],
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=finance
        )
        page_filter = SimpleNamespace(year=2026, with_deleted=False)

        service = FinanceService(repository=finance_repository_mock)
        service.repository.find_by_finance_year = AsyncMock(return_value=finance)
        service.find_one = AsyncMock()

        result = await service.find_by_user(
            current_user=current_user,
            page_filter=page_filter,
        )

        assert result == finance
        service.repository.find_by_finance_year.assert_awaited_once_with(
            finance_id=finance.id,
            reference_year=2026,
            with_deleted=False,
        )
        service.find_one.assert_not_awaited()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_find_by_user_service_with_year_not_found(
        finance_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=finance
        )
        page_filter = SimpleNamespace(year=2026, with_deleted=False)

        service = FinanceService(repository=finance_repository_mock)
        service.repository.find_by_finance_year = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await service.find_by_user(
                current_user=current_user, page_filter=page_filter
            )

        assert exc_info.value.status_code == HTTPStatus.NOT_FOUND
        assert exc_info.value.detail == "Finance not found"

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_find_by_user_service_with_year_empty_data_not_found(
        finance_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=finance
        )
        page_filter = SimpleNamespace(year=2025, with_deleted=False)
        filtered_finance = SimpleNamespace(
            id=finance.id,
            incomes=[],
            expenses=[],
            allocation_contributions=[],
            allocations=[],
        )

        service = FinanceService(repository=finance_repository_mock)
        service.repository.find_by_finance_year = AsyncMock(
            return_value=filtered_finance
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.find_by_user(
                current_user=current_user, page_filter=page_filter
            )

        assert exc_info.value.status_code == HTTPStatus.NOT_FOUND
        assert exc_info.value.detail == "Finance not found"


class TestFinancePersistService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_persist_with_single_payload_success(
        finance_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        income = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())
        expense = SimpleNamespace(id=uuid4(), category=SimpleNamespace(id=uuid4()))

        account_service_mock = AsyncMock()
        account_service_mock.persist.return_value = account

        income_service_mock = AsyncMock()
        income_service_mock.persist.return_value = income

        allocation_service_mock = AsyncMock()
        allocation_service_mock.persist.return_value = allocation

        expense_service_mock = AsyncMock()
        expense_service_mock.persist_by_category.return_value = [expense]

        service = FinanceService(
            repository=finance_repository_mock,
            account_service=account_service_mock,
            income_service=income_service_mock,
            allocation_service=allocation_service_mock,
            expense_service=expense_service_mock,
        )

        payloads = [
            SimpleNamespace(
                name="Test Account",
                type="BANK",
                initial_balance=1000,
                reference_day=10,
                reference_year=2026,
                incomes=[
                    SimpleNamespace(
                        months=[1, 2, 3],
                        source="Salary",
                        description="Monthly salary",
                    )
                ],
                allocations=[
                    SimpleNamespace(
                        name="Test Allocation",
                        type="HOUSE",
                        description="Savings goal",
                        categories=[SimpleNamespace()],
                    )
                ],
            )
        ]

        result = await service.persist(finance=finance, payloads=payloads)

        assert result.accounts == 1
        assert result.incomes == 1
        assert result.allocations == 1
        assert result.expenses == 1
        assert result.categories == 1

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_persist_with_multiple_payloads(
        finance_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account1 = SimpleNamespace(id=uuid4())
        account2 = SimpleNamespace(id=uuid4())
        income = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())
        expense = SimpleNamespace(id=uuid4(), category=SimpleNamespace(id=uuid4()))

        account_service_mock = AsyncMock()
        account_service_mock.persist.side_effect = [account1, account2]

        income_service_mock = AsyncMock()
        income_service_mock.persist.side_effect = [income, income]

        allocation_service_mock = AsyncMock()
        allocation_service_mock.persist.side_effect = [allocation, allocation]

        expense_service_mock = AsyncMock()
        expense_service_mock.persist_by_category.side_effect = [
            [expense],
            [expense],
        ]

        service = FinanceService(
            repository=finance_repository_mock,
            account_service=account_service_mock,
            income_service=income_service_mock,
            allocation_service=allocation_service_mock,
            expense_service=expense_service_mock,
        )

        payloads = [
            SimpleNamespace(
                name="Account 1",
                type="BANK",
                initial_balance=1000,
                reference_day=10,
                reference_year=2026,
                incomes=[
                    SimpleNamespace(
                        months=[1],
                        source="Salary",
                        description="Income 1",
                    )
                ],
                allocations=[
                    SimpleNamespace(
                        name="Allocation 1",
                        type="HOUSE",
                        description="Allocation 1",
                        categories=[SimpleNamespace()],
                    )
                ],
            ),
            SimpleNamespace(
                name="Account 2",
                type="PIX",
                initial_balance=5000,
                reference_day=15,
                reference_year=2026,
                incomes=[
                    SimpleNamespace(
                        months=[2],
                        source="Bonus",
                        description="Income 2",
                    )
                ],
                allocations=[
                    SimpleNamespace(
                        name="Allocation 2",
                        type="FAMILY",
                        description="Allocation 2",
                        categories=[SimpleNamespace()],
                    )
                ],
            ),
        ]

        result = await service.persist(finance=finance, payloads=payloads)

        assert result.accounts == 2
        assert result.incomes == 2
        assert result.allocations == 2
        assert result.expenses == 2
        assert result.categories == 2

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_persist_with_no_initial_balance(
        finance_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())

        account_service_mock = AsyncMock()
        account_service_mock.persist.return_value = account

        income_service_mock = AsyncMock()
        income_service_mock.persist.return_value = SimpleNamespace(id=uuid4())

        allocation_service_mock = AsyncMock()
        expense_service_mock = AsyncMock()
        expense_service_mock.persist_by_category.return_value = []

        service = FinanceService(
            repository=finance_repository_mock,
            account_service=account_service_mock,
            income_service=income_service_mock,
            allocation_service=allocation_service_mock,
            expense_service=expense_service_mock,
        )

        payloads = [
            SimpleNamespace(
                name="Account",
                type="CASH",
                initial_balance=None,
                reference_day=10,
                reference_year=2026,
                incomes=[],
                allocations=[],
            )
        ]

        await service.persist(finance=finance, payloads=payloads)

        account_service_mock.persist.assert_called_once()
        call_args = account_service_mock.persist.call_args
        assert call_args.kwargs["payload"].initial_balance == 0

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_persist_with_no_reference_day(
        finance_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())

        account_service_mock = AsyncMock()
        account_service_mock.persist.return_value = account

        income_service_mock = AsyncMock()
        income_service_mock.persist.return_value = SimpleNamespace(id=uuid4())

        allocation_service_mock = AsyncMock()
        expense_service_mock = AsyncMock()
        expense_service_mock.persist_by_category.return_value = []

        service = FinanceService(
            repository=finance_repository_mock,
            account_service=account_service_mock,
            income_service=income_service_mock,
            allocation_service=allocation_service_mock,
            expense_service=expense_service_mock,
        )

        payloads = [
            SimpleNamespace(
                name="Account",
                type="INVESTMENT",
                initial_balance=1000,
                reference_day=None,
                reference_year=2026,
                incomes=[],
                allocations=[],
            )
        ]

        await service.persist(finance=finance, payloads=payloads)

        income_service_mock.persist.assert_not_called()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_persist_with_multiple_incomes(
        finance_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        income = SimpleNamespace(id=uuid4())

        account_service_mock = AsyncMock()
        account_service_mock.persist.return_value = account

        income_service_mock = AsyncMock()
        income_service_mock.persist.side_effect = [income, income]

        allocation_service_mock = AsyncMock()
        expense_service_mock = AsyncMock()
        expense_service_mock.persist_by_category.return_value = []

        service = FinanceService(
            repository=finance_repository_mock,
            account_service=account_service_mock,
            income_service=income_service_mock,
            allocation_service=allocation_service_mock,
            expense_service=expense_service_mock,
        )

        payloads = [
            SimpleNamespace(
                name="Account",
                type="OTHER",
                initial_balance=1000,
                reference_day=10,
                reference_year=2026,
                incomes=[
                    SimpleNamespace(
                        months=[1, 2],
                        source="Salary",
                        description="Main income",
                    ),
                    SimpleNamespace(
                        months=[3],
                        source="Bonus",
                        description="Bonus income",
                    ),
                ],
                allocations=[],
            )
        ]

        result = await service.persist(finance=finance, payloads=payloads)

        assert result.incomes == 2
        assert income_service_mock.persist.call_count == 2

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_persist_with_multiple_allocations(
        finance_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())
        expense_without_category = SimpleNamespace(id=uuid4(), category=None)
        expense_with_category = SimpleNamespace(
            id=uuid4(), category=SimpleNamespace(id=uuid4())
        )

        account_service_mock = AsyncMock()
        account_service_mock.persist.return_value = account

        income_service_mock = AsyncMock()
        allocation_service_mock = AsyncMock()
        allocation_service_mock.persist.side_effect = [allocation, allocation]

        expense_service_mock = AsyncMock()
        expense_service_mock.persist_by_category.side_effect = [
            [expense_with_category],
            [expense_without_category],
        ]

        service = FinanceService(
            repository=finance_repository_mock,
            account_service=account_service_mock,
            income_service=income_service_mock,
            allocation_service=allocation_service_mock,
            expense_service=expense_service_mock,
        )

        payloads = [
            SimpleNamespace(
                name="Account",
                type="ACCOUNT_DEBIT",
                initial_balance=1000,
                reference_day=10,
                reference_year=2026,
                incomes=[],
                allocations=[
                    SimpleNamespace(
                        name="Allocation 1",
                        type="HOUSE",
                        description="Savings",
                        categories=[SimpleNamespace()],
                    ),
                    SimpleNamespace(
                        name="Allocation 2",
                        type="PERSONAL",
                        description=None,
                        categories=[SimpleNamespace()],
                    ),
                ],
            )
        ]

        result = await service.persist(finance=finance, payloads=payloads)

        assert result.allocations == 2
        assert result.expenses == 2
        assert result.categories == 1

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_persist_with_default_allocation_description(
        finance_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())

        account_service_mock = AsyncMock()
        account_service_mock.persist.return_value = account

        income_service_mock = AsyncMock()
        allocation_service_mock = AsyncMock()
        allocation_service_mock.persist.return_value = allocation

        expense_service_mock = AsyncMock()
        expense_service_mock.persist_by_category.return_value = []

        service = FinanceService(
            repository=finance_repository_mock,
            account_service=account_service_mock,
            income_service=income_service_mock,
            allocation_service=allocation_service_mock,
            expense_service=expense_service_mock,
        )

        payloads = [
            SimpleNamespace(
                name="Account",
                type="PIX",
                initial_balance=1000,
                reference_day=10,
                reference_year=2026,
                incomes=[],
                allocations=[
                    SimpleNamespace(
                        name="Allocation Name",
                        type="FAMILY",
                        description=None,
                        categories=[SimpleNamespace()],
                    )
                ],
            )
        ]

        await service.persist(finance=finance, payloads=payloads)

        allocation_service_mock.persist.assert_called_once()
        call_args = allocation_service_mock.persist.call_args
        assert call_args.kwargs["payload"].description == "Allocation Name"

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_persist_empty_payloads(
        finance_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())

        service = FinanceService(repository=finance_repository_mock)

        payloads: list = []

        result = await service.persist(finance=finance, payloads=payloads)

        assert result.incomes == 0
        assert result.accounts == 0
        assert result.expenses == 0
        assert result.categories == 0
        assert result.allocations == 0
