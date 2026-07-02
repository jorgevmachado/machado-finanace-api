from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.domain.finance.allocation_contribution.schema import (
    PayloadAllocationContributionCreateSchema,
)
from app.domain.finance.allocation_contribution.service import (
    AllocationContributionService,
)
from app.domain.finance.expense_month.schema import PayloadExpenseMonthPersistSchema
from app.domain.finance.schema import FinanceCreateContributionsSchema

from app.models import utcnow


@pytest.fixture
def allocation_contribution_repository_mock() -> AsyncMock:
    return AsyncMock()


class TestFinanceAllocationContributionFromSessionService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_from_session_builds_service() -> None:
        service = AllocationContributionService.from_session(AsyncMock())
        assert isinstance(service, AllocationContributionService)


class TestFinanceAllocationContributionCreateService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_allocation_contribution_create_with_invalid_account(
        allocation_contribution_repository_mock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())
        current_year = utcnow().year
        payload = PayloadAllocationContributionCreateSchema(
            months=[],
            account_id=account.id,
            description="Some Description",
            allocation_id=allocation.id,
            reference_day=10,
            reference_year=current_year,
            contributor_name="Some Name",
        )

        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )

        service.account_service.find_by = AsyncMock(return_value=None)
        service.allocation_service.find_by = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail == f"Account with this id {account.id} does not exist"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_allocation_contribution_create_with_invalid_allocation(
        allocation_contribution_repository_mock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())
        current_year = utcnow().year
        payload = PayloadAllocationContributionCreateSchema(
            months=[],
            account_id=account.id,
            description="Some Description",
            allocation_id=allocation.id,
            reference_day=10,
            reference_year=current_year,
            contributor_name="Some Name",
        )

        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )

        service.account_service.find_by = AsyncMock(return_value=account)
        service.allocation_service.find_by = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Allocation with this id {allocation.id} does not exist"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_allocation_contribution_create_with_existing_allocation_contribution(
        allocation_contribution_repository_mock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())
        current_year = utcnow().year
        payload = PayloadAllocationContributionCreateSchema(
            months=[],
            account_id=account.id,
            description="Some Description",
            allocation_id=allocation.id,
            reference_day=10,
            reference_year=current_year,
            contributor_name="Some Name",
        )

        existing_allocation_contribution = SimpleNamespace(
            id=uuid4(),
            account_id=account.id,
            allocation_id=allocation.id,
        )

        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )

        service.account_service.find_by = AsyncMock(return_value=account)
        service.allocation_service.find_by = AsyncMock(return_value=allocation)
        service.find_by = AsyncMock(return_value=existing_allocation_contribution)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST

    @staticmethod
    @pytest.mark.asyncio
    async def test_allocation_contribution_create_successfully(
        allocation_contribution_repository_mock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())
        current_year = utcnow().year
        payload = PayloadAllocationContributionCreateSchema(
            months=[],
            account_id=account.id,
            description="Some Description",
            allocation_id=allocation.id,
            reference_day=10,
            reference_year=current_year,
            contributor_name="Some Name",
        )

        saved_allocation_contribution = SimpleNamespace(
            id=uuid4(),
            account_id=account.id,
            allocation_id=allocation.id,
        )

        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )

        service.account_service.find_by = AsyncMock(return_value=account)
        service.allocation_service.find_by = AsyncMock(return_value=allocation)
        service.find_by = AsyncMock(side_effect=[None, saved_allocation_contribution])
        service.allocation_contribution_month_service.persist_list = AsyncMock(
            return_value=[]
        )
        allocation_contribution_repository_mock.save.return_value = (
            saved_allocation_contribution
        )

        result = await service.create(finance=finance, payload=payload)
        assert result == saved_allocation_contribution


class TestFinanceAllocationContributionPersistService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_allocation_contribution_persist_invalid_year(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())
        current_year = utcnow().year
        payload = PayloadAllocationContributionCreateSchema(
            months=[],
            account_id=uuid4(),
            description="Some Description",
            allocation_id=uuid4(),
            reference_day=10,
            reference_year=current_year + 1,
            contributor_name="Some Name",
        )

        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock,
            account_service=AsyncMock(),
            allocation_contribution_month_service=AsyncMock(),
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.persist(
                payload=payload,
                account=account,
                finance=finance,
                allocation=allocation,
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST

    @staticmethod
    @pytest.mark.asyncio
    async def test_allocation_contribution_persist_exist_allocation_contribution_with_throw(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())
        current_year = utcnow().year
        payload = PayloadAllocationContributionCreateSchema(
            months=[],
            account_id=uuid4(),
            description="Some Description",
            allocation_id=uuid4(),
            reference_day=10,
            reference_year=current_year,
            contributor_name="Some Name",
        )

        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock,
            account_service=AsyncMock(),
            allocation_contribution_month_service=AsyncMock(),
        )
        service.find_by = AsyncMock(return_value=SimpleNamespace(id=uuid4()))

        with pytest.raises(HTTPException) as exc_info:
            await service.persist(
                payload=payload,
                account=account,
                finance=finance,
                allocation=allocation,
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Allocation Contribution with this year {payload.reference_year} and name {payload.contributor_name} already exists"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_allocation_contribution_persist_exist_allocation_contribution_without_throw(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())
        current_year = utcnow().year
        payload = PayloadAllocationContributionCreateSchema(
            months=[],
            account_id=uuid4(),
            description="Some Description",
            allocation_id=uuid4(),
            reference_day=10,
            reference_year=current_year,
            contributor_name="Some Name",
        )

        exist_allocation_contribution = SimpleNamespace(
            id=uuid4(),
            account_id=account.id,
            allocation_id=allocation.id,
        )

        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock,
            account_service=AsyncMock(),
            allocation_contribution_month_service=AsyncMock(),
        )

        service.find_by = AsyncMock(return_value=exist_allocation_contribution)
        service.allocation_contribution_month_service.persist_list = AsyncMock(
            return_value=[]
        )
        service.repository.update.return_value = exist_allocation_contribution
        result = await service.persist(
            payload=payload,
            account=account,
            finance=finance,
            allocation=allocation,
            with_throw=False,
        )
        assert result == exist_allocation_contribution

    @staticmethod
    @pytest.mark.asyncio
    async def test_allocation_contribution_persist_allocation_contribution_successfully(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())
        current_year = utcnow().year
        payload = PayloadAllocationContributionCreateSchema(
            months=[],
            account_id=uuid4(),
            description="Some Description",
            allocation_id=uuid4(),
            reference_day=10,
            reference_year=current_year,
            contributor_name="Some Name",
        )

        saved_allocation_contribution = SimpleNamespace(
            id=uuid4(),
            account_id=account.id,
            allocation_id=allocation.id,
        )

        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock,
            account_service=AsyncMock(),
            allocation_contribution_month_service=AsyncMock(),
        )

        service.find_by = AsyncMock(side_effect=[None, saved_allocation_contribution])
        service.allocation_contribution_month_service.persist_list = AsyncMock(
            return_value=[]
        )
        service.repository.save.return_value = saved_allocation_contribution
        result = await service.persist(
            payload=payload,
            account=account,
            finance=finance,
            allocation=allocation,
            with_throw=False,
        )
        assert result == saved_allocation_contribution


class TestFinanceAllocationContributionCreateByAccountService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_allocation_contribution_create_by_account_empty_list(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())

        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )

        result = await service.create_by_account(
            finance=finance,
            account=account,
            allocation=allocation,
            reference_day=10,
            reference_year=2026,
            payload_allocation_contributions=[],
        )

        assert result == []
        allocation_contribution_repository_mock.save.assert_not_awaited()

    @staticmethod
    @pytest.mark.asyncio
    async def test_allocation_contribution_create_by_account_with_single_payload(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())

        created_allocation_contribution = SimpleNamespace(
            id=uuid4(), contributor_name="Test Contributor"
        )

        payload_allocation_contributions = [
            FinanceCreateContributionsSchema(
                months=[
                    PayloadExpenseMonthPersistSchema(
                        amount=5000,
                        reference_month=1,
                    )
                ],
                description="Test Description",
                contributor_name="Test Contributor",
            )
        ]

        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )

        allocation_contribution_repository_mock.find_by.side_effect = [
            None,
            created_allocation_contribution,
        ]
        allocation_contribution_repository_mock.save.return_value = (
            created_allocation_contribution
        )
        service.allocation_contribution_month_service.persist_list = AsyncMock(
            return_value=[]
        )

        result = await service.create_by_account(
            finance=finance,
            account=account,
            allocation=allocation,
            reference_day=10,
            reference_year=2026,
            payload_allocation_contributions=payload_allocation_contributions,
        )

        assert len(result) == 1
        assert result[0] == created_allocation_contribution

    @staticmethod
    @pytest.mark.asyncio
    async def test_allocation_contribution_create_by_account_with_multiple_payload(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())

        created_allocation_contribution_1 = SimpleNamespace(
            id=uuid4(), contributor_name="Test Contributor"
        )

        created_allocation_contribution_2 = SimpleNamespace(
            id=uuid4(), contributor_name="Test Contributor 2"
        )

        payload_allocation_contributions = [
            FinanceCreateContributionsSchema(
                months=[
                    PayloadExpenseMonthPersistSchema(
                        amount=5000,
                        reference_month=1,
                    ),
                    PayloadExpenseMonthPersistSchema(
                        amount=5000,
                        reference_month=2,
                    ),
                ],
                description="Test Description",
                contributor_name="Test Contributor",
            ),
            FinanceCreateContributionsSchema(
                months=[
                    PayloadExpenseMonthPersistSchema(
                        amount=2000,
                        reference_month=12,
                    )
                ],
                description="Test Description 2",
                contributor_name="Test Contributor 2",
            ),
        ]

        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )

        allocation_contribution_repository_mock.find_by.side_effect = [
            None,
            created_allocation_contribution_1,
            None,
            created_allocation_contribution_2,
        ]
        allocation_contribution_repository_mock.save.side_effect = [
            created_allocation_contribution_1,
            created_allocation_contribution_2,
        ]
        service.allocation_contribution_month_service.persist_list = AsyncMock(
            side_effect=[[], []]
        )

        result = await service.create_by_account(
            finance=finance,
            account=account,
            allocation=allocation,
            reference_day=10,
            reference_year=2026,
            payload_allocation_contributions=payload_allocation_contributions,
        )

        assert len(result) == 2
        assert result[0] == created_allocation_contribution_1
        assert result[1] == created_allocation_contribution_2
        assert allocation_contribution_repository_mock.save.await_count == 2

    @staticmethod
    @pytest.mark.asyncio
    async def test_allocation_contribution_create_by_account_with_no_months_in_payload(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())

        created_allocation_contribution = SimpleNamespace(
            id=uuid4(), contributor_name="Test Contributor"
        )

        payload_allocation_contributions = [
            FinanceCreateContributionsSchema(
                months=[],
                description="Test Description",
                contributor_name="Test Contributor",
            )
        ]

        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )

        allocation_contribution_repository_mock.find_by.side_effect = [
            None,
            created_allocation_contribution,
        ]
        allocation_contribution_repository_mock.save.return_value = (
            created_allocation_contribution
        )
        service.allocation_contribution_month_service.persist_list = AsyncMock(
            return_value=[]
        )

        result = await service.create_by_account(
            finance=finance,
            account=account,
            allocation=allocation,
            reference_day=10,
            reference_year=2026,
            payload_allocation_contributions=payload_allocation_contributions,
        )

        assert len(result) == 1
        assert result[0] == created_allocation_contribution
        assert allocation_contribution_repository_mock.save.await_count == 1
