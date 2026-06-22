from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4


import pytest
from fastapi import HTTPException

from app.domain.finance.allocation.schema import PayloadAllocationCreateSchema
from app.domain.finance.allocation.service import AllocationService
from app.models import AllocationTypeEnum


@pytest.fixture
def allocation_repository_mock() -> AsyncMock:
    return AsyncMock()


class TestFinanceAllocationServiceFromSession:
    @staticmethod
    @pytest.mark.asyncio
    async def test_from_session_builds_service() -> None:
        service = AllocationService.from_session(AsyncMock())
        assert isinstance(service, AllocationService)


class TestFinanceAllocationCreateService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_service_create_not_has_finance(
        allocation_repository_mock: AsyncMock,
    ):
        payload = PayloadAllocationCreateSchema(
            name="Test Allocation",
            type=AllocationTypeEnum.OTHER,
            description="Some Description",
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=None
        )

        service = AllocationService(repository=allocation_repository_mock)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "User must be onboarded first"

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_service_create_already_exist_account(
        allocation_repository_mock: AsyncMock,
    ):
        payload = PayloadAllocationCreateSchema(
            name="Test Allocation",
            type=AllocationTypeEnum.OTHER,
            description="Some Description",
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = AllocationService(repository=allocation_repository_mock)
        service.find_by = AsyncMock(return_value=SimpleNamespace(id=uuid4()))

        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "Allocation with this name already exists"

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_service_create_successfully(
        allocation_repository_mock: AsyncMock,
    ):
        payload = PayloadAllocationCreateSchema(
            name="Test Allocation",
            type=AllocationTypeEnum.OTHER,
            description="Some Description",
        )
        finance_id = uuid4()
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=finance_id)
        )
        allocation = SimpleNamespace(id=uuid4(), finance_id=finance_id)

        service = AllocationService(repository=allocation_repository_mock)
        service.find_by = AsyncMock(return_value=None)

        allocation_repository_mock.save.return_value = allocation

        result = await service.create(current_user=current_user, payload=payload)
        assert result == allocation
