from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.domain.finance.allocation.schema import (
    PayloadAllocationCreateSchema,
)
from app.domain.finance.allocation.service import AllocationService
from app.models import AllocationTypeEnum
from app.shared.utils.string import to_snake_case


@pytest.fixture
def allocation_repository_mock() -> AsyncMock:
    return AsyncMock()


class TestFinanceAllocationServiceFromSession:
    @staticmethod
    @pytest.mark.asyncio
    async def test_from_session_builds_service() -> None:
        service = AllocationService.from_session(AsyncMock())
        assert isinstance(service, AllocationService)


class TestFinanceAllocationPersistService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_raises_when_allocation_exists(
        allocation_repository_mock: AsyncMock,
    ):
        payload = PayloadAllocationCreateSchema(
            name="Test Allocation",
            type=AllocationTypeEnum.OTHER,
            description="Some Description",
        )
        finance = SimpleNamespace(id=uuid4())
        service = AllocationService(repository=allocation_repository_mock)
        service.find_by = AsyncMock(return_value=SimpleNamespace(id=uuid4()))

        with pytest.raises(HTTPException) as exc_info:
            await service.persist(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "Allocation with this name already exists"

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_returns_existing_when_with_throw_false(
        allocation_repository_mock: AsyncMock,
    ):
        payload = PayloadAllocationCreateSchema(
            name="Test Allocation",
            type=AllocationTypeEnum.OTHER,
            description="Some Description",
        )
        finance = SimpleNamespace(id=uuid4())
        existing = SimpleNamespace(id=uuid4())
        service = AllocationService(repository=allocation_repository_mock)
        service.find_by = AsyncMock(return_value=existing)

        result = await service.persist(
            finance=finance, payload=payload, with_throw=False
        )

        assert result is existing
        allocation_repository_mock.save.assert_not_awaited()

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_successfully_saves(allocation_repository_mock: AsyncMock):
        payload = PayloadAllocationCreateSchema(
            name="Test Allocation",
            type=AllocationTypeEnum.OTHER,
            description="Some Description",
        )
        finance_id = uuid4()
        finance = SimpleNamespace(id=finance_id)
        expected = SimpleNamespace(id=uuid4())
        service = AllocationService(repository=allocation_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        allocation_repository_mock.save.return_value = expected

        result = await service.persist(finance=finance, payload=payload)

        assert result is expected
        allocation_repository_mock.save.assert_awaited_once()
        saved_entity = allocation_repository_mock.save.await_args.kwargs["entity"]
        assert saved_entity.finance_id == finance_id
        assert saved_entity.name == payload.name
        assert saved_entity.name_code == to_snake_case(payload.name)
        assert saved_entity.type == payload.type
        assert saved_entity.is_active is True
        assert saved_entity.description == payload.description
