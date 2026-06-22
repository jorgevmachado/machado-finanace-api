from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4


import pytest
from fastapi import HTTPException

from app.domain.finance.account.schema import PayloadAccountCreateSchema
from app.domain.finance.account.service import AccountService
from app.models import AccountTypeEnum


@pytest.fixture
def account_repository_mock() -> AsyncMock:
    return AsyncMock()


class TestFinanceAccountServiceFromSession:
    @staticmethod
    @pytest.mark.asyncio
    async def test_from_session_builds_service() -> None:
        service = AccountService.from_session(AsyncMock())
        assert isinstance(service, AccountService)


class TestFinanceAccountCreateService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_account_service_create_not_has_finance(
        account_repository_mock: AsyncMock,
    ):
        payload = PayloadAccountCreateSchema(
            name="Test Account",
            type=AccountTypeEnum.BANK,
            initial_balance=100.0
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=None
        )

        service = AccountService(repository=account_repository_mock)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail == "User must be onboarded first"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_account_service_create_already_exist_account(
        account_repository_mock: AsyncMock,
    ):
        payload = PayloadAccountCreateSchema(
            name="Test Account", type=AccountTypeEnum.BANK, initial_balance=100.0
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = AccountService(repository=account_repository_mock)
        service.find_by = AsyncMock(return_value=SimpleNamespace(id=uuid4()))

        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "Account with this name already exists"

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_account_service_create_successfully(
        account_repository_mock: AsyncMock,
    ):
        payload = PayloadAccountCreateSchema(
            name="Test Account", type=AccountTypeEnum.BANK, initial_balance=100.0
        )
        finance_id = uuid4()
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=finance_id)
        )
        account = SimpleNamespace(id=uuid4(), finance_id=finance_id)

        service = AccountService(repository=account_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        
        account_repository_mock.save.return_value = account

        result = await service.create(current_user=current_user, payload=payload)
        assert result == account
