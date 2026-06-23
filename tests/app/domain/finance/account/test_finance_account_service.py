from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.domain.finance.account.schema import (
    PayloadAccountCreateListSchema,
    PayloadAccountCreateSchema,
)
from app.domain.finance.account.service import AccountService
from app.models import AccountTypeEnum
from app.shared.utils.string import to_snake_case


@pytest.fixture
def account_repository_mock() -> AsyncMock:
    return AsyncMock()


class TestFinanceAccountServiceFromSession:
    @staticmethod
    @pytest.mark.asyncio
    async def test_from_session_builds_service() -> None:
        service = AccountService.from_session(AsyncMock())
        assert isinstance(service, AccountService)


class TestFinanceAccountPersistService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_create_delegates_to_persist(account_repository_mock: AsyncMock):
        payload = PayloadAccountCreateSchema(
            name="Test Account", type=AccountTypeEnum.BANK, initial_balance=100.0
        )
        finance = SimpleNamespace(id=uuid4())
        expected = SimpleNamespace(id=uuid4())
        service = AccountService(repository=account_repository_mock)
        service.persist = AsyncMock(return_value=expected)

        result = await service.create(finance=finance, payload=payload)

        assert result is expected
        service.persist.assert_awaited_once_with(finance=finance, payload=payload)

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_raises_when_account_exists(account_repository_mock: AsyncMock):
        payload = PayloadAccountCreateSchema(
            name="Test Account", type=AccountTypeEnum.BANK, initial_balance=100.0
        )
        finance = SimpleNamespace(id=uuid4())
        service = AccountService(repository=account_repository_mock)
        service.find_by = AsyncMock(return_value=SimpleNamespace(id=uuid4()))

        with pytest.raises(HTTPException) as exc_info:
            await service.persist(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Account with this name {payload.name} already exists"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_returns_existing_when_with_throw_false(
        account_repository_mock: AsyncMock,
    ):
        payload = PayloadAccountCreateSchema(
            name="Test Account", type=AccountTypeEnum.BANK, initial_balance=100.0
        )
        finance = SimpleNamespace(id=uuid4())
        existing = SimpleNamespace(id=uuid4())
        service = AccountService(repository=account_repository_mock)
        service.find_by = AsyncMock(return_value=existing)

        result = await service.persist(finance=finance, payload=payload, with_throw=False)

        assert result is existing
        account_repository_mock.save.assert_not_awaited()

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_successfully_saves(account_repository_mock: AsyncMock):
        payload = PayloadAccountCreateSchema(
            name="Test Account", type=AccountTypeEnum.BANK, initial_balance=100.0
        )
        finance_id = uuid4()
        finance = SimpleNamespace(id=finance_id)
        expected = SimpleNamespace(id=uuid4())
        service = AccountService(repository=account_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        account_repository_mock.save.return_value = expected

        result = await service.persist(finance=finance, payload=payload)

        assert result is expected
        account_repository_mock.save.assert_awaited_once()
        saved_entity = account_repository_mock.save.await_args.kwargs["entity"]
        assert saved_entity.finance_id == finance_id
        assert saved_entity.name == payload.name
        assert saved_entity.name_code == to_snake_case(payload.name)
        assert saved_entity.type == payload.type
        assert saved_entity.is_active is True
        assert saved_entity.initial_balance == payload.initial_balance
        assert saved_entity.current_balance == payload.initial_balance

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_list_raises_for_empty_payload(account_repository_mock: AsyncMock):
        service = AccountService(repository=account_repository_mock)
        payload = PayloadAccountCreateListSchema(accounts=[])

        with pytest.raises(HTTPException) as exc_info:
            await service.create_list(finance=SimpleNamespace(id=uuid4()), payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "Accounts list cannot be empty"

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_list_calls_persist_for_each_item(
        account_repository_mock: AsyncMock,
    ):
        service = AccountService(repository=account_repository_mock)
        finance = SimpleNamespace(id=uuid4())
        payload = PayloadAccountCreateListSchema(
            accounts=[
                PayloadAccountCreateSchema(
                    name="Conta A", type=AccountTypeEnum.BANK, initial_balance=100.0
                ),
                PayloadAccountCreateSchema(
                    name="Conta B", type=AccountTypeEnum.OTHER, initial_balance=50.0
                ),
            ]
        )
        expected = [SimpleNamespace(id=uuid4()), SimpleNamespace(id=uuid4())]
        service.persist = AsyncMock(side_effect=expected)

        result = await service.create_list(finance=finance, payload=payload)

        assert result == expected
        assert service.persist.await_count == 2
        first_call = service.persist.await_args_list[0].kwargs
        second_call = service.persist.await_args_list[1].kwargs
        assert first_call["finance"] is finance
        assert first_call["payload"] == payload.accounts[0]
        assert first_call["with_throw"] is False
        assert second_call["payload"] == payload.accounts[1]
