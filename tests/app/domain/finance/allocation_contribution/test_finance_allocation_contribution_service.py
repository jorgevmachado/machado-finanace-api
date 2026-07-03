from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.domain.finance.allocation_contribution.schema import (
    PayloadAllocationContributionCreateSchema,
)
from app.domain.finance.allocation_contribution.service import (
    AllocationContributionService,
)
from app.domain.finance.months.schema import PayloadMonthPersistSchema
from app.models import Account, Allocation, Finance, utcnow


@pytest.fixture
def finance():
    finance = MagicMock(spec=Finance)
    finance.id = uuid4()
    return finance


@pytest.fixture
def account():
    account = MagicMock(spec=Account)
    account.id = uuid4()
    account.finance_id = uuid4()
    return account


@pytest.fixture
def allocation():
    allocation = MagicMock(spec=Allocation)
    allocation.id = uuid4()
    return allocation


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
        allocation_contribution_repository_mock, finance, account, allocation
    ):
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
        allocation_contribution_repository_mock, finance, account, allocation
    ):
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
        allocation_contribution_repository_mock, finance, account, allocation
    ):
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
        allocation_contribution_repository_mock, finance, account, allocation
    ):
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
    async def test_finance_allocation_contribution_persist_service_invalid_year(
        allocation_contribution_repository_mock, finance, account, allocation
    ):
        months = [
            PayloadMonthPersistSchema(
                amount=100.00,
                reference_month=1,
                transaction_date=None,
            ),
            PayloadMonthPersistSchema(
                amount=150.00,
                reference_month=6,
                transaction_date=None,
            ),
        ]
        description = "Some Description"
        current_year = utcnow().year
        reference_day = 10
        reference_year = current_year + 1
        contributor_name = "Some Contributor Name"

        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.persist(
                months=months,
                finance=finance,
                account=account,
                allocation=allocation,
                with_throw=True,
                description=description,
                reference_day=reference_day,
                reference_year=reference_year,
                contributor_name=contributor_name,
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Reference year {reference_year} must be less than or equal to the current year {current_year}"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_contribution_persist_service_exist_allocation_contribution_with_throw(
        allocation_contribution_repository_mock, finance, account, allocation
    ):
        months = [
            PayloadMonthPersistSchema(
                amount=100.00,
                reference_month=1,
                transaction_date=None,
            ),
            PayloadMonthPersistSchema(
                amount=150.00,
                reference_month=6,
                transaction_date=None,
            ),
        ]
        description = "Some Description"
        current_year = utcnow().year
        reference_day = 10
        reference_year = current_year
        contributor_name = "Some Contributor Name"

        exist_allocation_contribution = SimpleNamespace(
            id=uuid4(),
            account_id=account.id,
            description=description,
            allocation_id=allocation.id,
            contributor_name=contributor_name,
        )
        allocation_contribution_repository_mock.find_by.return_value = (
            exist_allocation_contribution
        )
        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.persist(
                months=months,
                finance=finance,
                account=account,
                allocation=allocation,
                with_throw=True,
                description=description,
                reference_day=reference_day,
                reference_year=reference_year,
                contributor_name=contributor_name,
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Allocation Contribution with this year {current_year} and name {contributor_name} already exists"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_contribution_persist_service_exist_allocation_contribution_without_throw(
        allocation_contribution_repository_mock, finance, account, allocation
    ):
        months = [
            PayloadMonthPersistSchema(
                amount=100.00,
                reference_month=1,
                transaction_date=None,
            ),
            PayloadMonthPersistSchema(
                amount=150.00,
                reference_month=6,
                transaction_date=None,
            ),
        ]
        description = "Some Description"
        current_year = utcnow().year
        reference_day = 10
        reference_year = current_year
        contributor_name = "Some Contributor Name"

        exist_allocation_contribution = SimpleNamespace(
            id=uuid4(),
            account_id=account.id,
            description=description,
            allocation_id=allocation.id,
            contributor_name=contributor_name,
        )
        allocation_contribution_repository_mock.find_by.return_value = (
            exist_allocation_contribution
        )
        allocation_contribution_repository_mock.update.return_value = (
            exist_allocation_contribution
        )
        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )
        service.allocation_contribution_month_service.persist_list = AsyncMock(
            return_value=months
        )
        result = await service.persist(
            months=months,
            finance=finance,
            account=account,
            allocation=allocation,
            with_throw=False,
            description=description,
            reference_day=reference_day,
            reference_year=reference_year,
            contributor_name=contributor_name,
        )

        assert result == exist_allocation_contribution

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_contribution_persist_service_save_when_not_exist_allocation_contribution(
        allocation_contribution_repository_mock, finance, account, allocation
    ):
        months = [
            PayloadMonthPersistSchema(
                amount=100.00,
                reference_month=1,
                transaction_date=None,
            ),
            PayloadMonthPersistSchema(
                amount=150.00,
                reference_month=6,
                transaction_date=None,
            ),
        ]
        description = "Some Description"
        current_year = utcnow().year
        reference_day = 10
        reference_year = current_year
        contributor_name = "Some Contributor Name"

        created_allocation_contribution = SimpleNamespace(
            id=uuid4(),
            account_id=account.id,
            description=description,
            allocation_id=allocation.id,
            contributor_name=contributor_name,
        )

        allocation_contribution_repository_mock.save.return_value = (
            created_allocation_contribution
        )
        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )
        service.find_by = AsyncMock(side_effect=[None, created_allocation_contribution])
        service.allocation_contribution_month_service.persist_list = AsyncMock(
            return_value=months
        )
        result = await service.persist(
            months=months,
            finance=finance,
            account=account,
            allocation=allocation,
            with_throw=False,
            description=description,
            reference_day=reference_day,
            reference_year=reference_year,
            contributor_name=contributor_name,
        )

        assert result == created_allocation_contribution
        allocation_contribution_repository_mock.save.assert_awaited_once()
