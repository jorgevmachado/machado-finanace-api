from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.domain.finance.allocation.schema import (
    PayloadAllocationCreateSchema,
)
from app.domain.finance.allocation.service import AllocationService
from app.models import Account, Finance
from app.shared.utils.string import to_snake_case


@pytest.fixture
def allocation_repository_mock() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def account():
    account = MagicMock(spec=Account)
    account.id = uuid4()
    return account


@pytest.fixture
def finance():
    finance = MagicMock(spec=Finance)
    finance.id = uuid4()
    return finance


class TestFinanceAllocationServiceFromSession:
    @staticmethod
    @pytest.mark.asyncio
    async def test_from_session_builds_service() -> None:
        service = AllocationService.from_session(AsyncMock())
        assert isinstance(service, AllocationService)


class TestFinanceAllocationPersistService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_persist_raises_when_allocation_exists(
        allocation_repository_mock: AsyncMock, account
    ):
        service = AllocationService(repository=allocation_repository_mock)
        service.find_by = AsyncMock(return_value=SimpleNamespace(id=uuid4()))
        name = "Test Allocation"
        with pytest.raises(HTTPException) as exc_info:
            await service.persist(
                name=name,
                account=account,
                description="Some Description",
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail == f"Allocation with this name {name} already exists"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_persist_returns_existing_when_with_throw_false(
        allocation_repository_mock: AsyncMock, account
    ):
        existing = SimpleNamespace(id=uuid4())
        service = AllocationService(repository=allocation_repository_mock)
        service.find_by = AsyncMock(return_value=existing)

        result = await service.persist(
            name="Test Allocation",
            account=account,
            description="Some Description",
            with_throw=False,
        )

        assert result is existing
        allocation_repository_mock.save.assert_not_awaited()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_persist_successfully_saves(
        allocation_repository_mock: AsyncMock, account
    ):
        expected = SimpleNamespace(id=uuid4())
        service = AllocationService(repository=allocation_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        allocation_repository_mock.save.return_value = expected
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)

        result = await service.persist(
            name="Test Allocation",
            account=account,
            description="Some Description",
        )

        assert result is expected
        allocation_repository_mock.save.assert_awaited_once()
        saved_entity = allocation_repository_mock.save.await_args.kwargs["entity"]
        assert saved_entity.account_id == account.id
        assert saved_entity.name == "Test Allocation"
        assert saved_entity.name_code == to_snake_case("Test Allocation")
        assert saved_entity.is_active is True
        assert saved_entity.description == "Some Description"


class TestFinanceAllocationCreateService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_create_raises_when_account_not_found(
        allocation_repository_mock: AsyncMock, finance, account
    ):

        service = AllocationService(repository=allocation_repository_mock)
        service.account_service.find_by = AsyncMock(return_value=None)
        payload = PayloadAllocationCreateSchema(
            name="Test Allocation",
            account_id=account.id,
            description="Some Description",
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail == f"Account with this id {account.id} does not exist"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_create_successfully(
        allocation_repository_mock: AsyncMock, finance, account
    ):
        expected = SimpleNamespace(id=uuid4())

        service = AllocationService(repository=allocation_repository_mock)
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
        service.account_service.find_by = AsyncMock(return_value=account)
        service.find_by = AsyncMock(return_value=None)
        allocation_repository_mock.save.return_value = expected
        payload = PayloadAllocationCreateSchema(
            name="Test Allocation",
            account_id=account.id,
            description="Some Description",
        )
        result = await service.create(finance=finance, payload=payload)
        assert result is expected
        allocation_repository_mock.save.assert_awaited_once()
        saved_entity = allocation_repository_mock.save.await_args.kwargs["entity"]
        assert saved_entity.account_id == account.id
        assert saved_entity.name == "Test Allocation"
        assert saved_entity.name_code == to_snake_case("Test Allocation")
        assert saved_entity.is_active is True
        assert saved_entity.description == "Some Description"
