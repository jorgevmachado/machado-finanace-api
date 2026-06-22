from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4


import pytest
from fastapi import HTTPException

from app.domain.finance.allocation_contribution.schema import PayloadAllocationContributionCreateSchema
from app.domain.finance.allocation_contribution.service import AllocationContributionService
from app.models import utcnow

@pytest.fixture
def allocation_contribution_repository_mock() -> AsyncMock:
    return AsyncMock()


class TestFinanceIncomeServiceFromSession:
    @staticmethod
    @pytest.mark.asyncio
    async def test_from_session_builds_service() -> None:
        service = AllocationContributionService.from_session(AsyncMock())
        assert isinstance(service, AllocationContributionService)

class TestFinanceAllocationContributionCreateService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_contribution_service_create_not_has_finance(
        allocation_contribution_repository_mock: AsyncMock,
    ):

        current_year = utcnow().year
        payload = PayloadAllocationContributionCreateSchema(
            contributor_name="Contributor Name",
            amount=100.0,
            account_id=uuid4(),
            allocation_id=uuid4(),            
            description="Some Description",
            reference_year=current_year,
            reference_month=1,
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=None
        )

        service = AllocationContributionService(repository=allocation_contribution_repository_mock)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "User must be onboarded first"

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_contribution_service_create_invalid_year(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        current_year = utcnow().year
        year = current_year + 1
        payload = PayloadAllocationContributionCreateSchema(            
            contributor_name="Contributor Name",
            amount=100.0,
            account_id=uuid4(),
            allocation_id=uuid4(),
            description="Some Description",
            reference_year=year,
            reference_month=1,
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = AllocationContributionService(repository=allocation_contribution_repository_mock)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Reference year {year} must be less than or equal to the current year {current_year}"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_contribution_service_create_month_less_than_1(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        month = 0
        payload = PayloadAllocationContributionCreateSchema(            
            contributor_name="Contributor Name",
            amount=100.0,
            account_id=uuid4(),
            allocation_id=uuid4(),
            description="Some Description",
            reference_year=utcnow().year,
            reference_month=month,
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = AllocationContributionService(repository=allocation_contribution_repository_mock)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail == f"Reference month {month} must be between 1 and 12"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_contribution_service_create_month_bigger_than_12(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        month = 13
        payload = PayloadAllocationContributionCreateSchema(
            contributor_name="Contributor Name",
            amount=100.0,
            account_id=uuid4(),
            allocation_id=uuid4(),
            description="Some Description",
            reference_year=utcnow().year,
            reference_month=month,
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = AllocationContributionService(repository=allocation_contribution_repository_mock)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail == f"Reference month {month} must be between 1 and 12"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_contribution_service_create_exist(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        payload = PayloadAllocationContributionCreateSchema(
            contributor_name="Contributor Name",
            amount=100.0,
            account_id=uuid4(),
            allocation_id=uuid4(),
            description="Some Description",
            reference_year=utcnow().year,
            reference_month=1,
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = AllocationContributionService(repository=allocation_contribution_repository_mock)
        service.find_by = AsyncMock(return_value=SimpleNamespace(id=uuid4()))
        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Allocation Contribution with this year {payload.reference_year}, month {payload.reference_month} and name {payload.contributor_name} already exists"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_contribution_service_create_account_not_exist(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        payload = PayloadAllocationContributionCreateSchema(
            contributor_name="Contributor Name",
            amount=100.0,
            account_id=uuid4(),
            allocation_id=uuid4(),
            description="Some Description",
            reference_year=utcnow().year,
            reference_month=1,
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = AllocationContributionService(repository=allocation_contribution_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        service.account_service.find_by = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Account with this id {payload.account_id} does not exist"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_contribution_service_create_allocation_not_exist(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        payload = PayloadAllocationContributionCreateSchema(
            contributor_name="Contributor Name",
            amount=100.0,
            account_id=uuid4(),
            allocation_id=uuid4(),
            description="Some Description",
            reference_year=utcnow().year,
            reference_month=1,
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )
        service.find_by = AsyncMock(return_value=None)
        service.account_service.find_by = AsyncMock(return_value=SimpleNamespace(id=payload.account_id))
        service.allocation_service.find_by = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Allocation with this id {payload.allocation_id} does not exist"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_contribution_service_create_successfully(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        payload = PayloadAllocationContributionCreateSchema(
            contributor_name="Contributor Name",
            amount=100.0,
            account_id=uuid4(),
            allocation_id=uuid4(),
            description="Some Description",
            reference_year=utcnow().year,
            reference_month=1,
        )
        expected = SimpleNamespace(
            id=uuid4(),
            contributor_name="Contributor Name",
            amount=100.0,
            account_id=uuid4(),
            allocation_id=uuid4(),
            description="Some Description",
            reference_year=utcnow().year,
            reference_month=1,
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )
        service.find_by = AsyncMock(return_value=None)
        service.account_service.find_by = AsyncMock(
            return_value=SimpleNamespace(id=payload.account_id)
        )
        service.allocation_service.find_by = AsyncMock(
            return_value=SimpleNamespace(id=payload.allocation_id)
        )
        service.repository.save.return_value = expected
        result = await service.create(current_user=current_user, payload=payload)
        assert result == expected