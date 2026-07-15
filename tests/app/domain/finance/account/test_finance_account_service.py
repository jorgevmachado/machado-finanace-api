from types import SimpleNamespace
from uuid import uuid4

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.finance.account.repository import AccountRepository
from app.domain.finance.account.service import AccountService
from app.domain.finance.account.schema import PayloadAccountCreateSchema
from app.models import Account, Finance, AccountTypeEnum


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def account_service(mock_session):
    repository = AccountRepository(mock_session)
    return AccountService(repository)


@pytest.fixture
def account_repository_mock() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def finance():
    finance = MagicMock(spec=Finance)
    finance.id = "test-finance-id"
    return finance


@pytest.fixture
def account():
    account = MagicMock(spec=Account)
    account.id = "test-account-id"
    account.finance_id = "test-finance-id"
    account.name = "Test Account"
    account.name_code = "test_account"
    account.type = AccountTypeEnum.BANK
    account.is_active = True
    account.initial_balance = Decimal("1000.00")
    account.current_balance = Decimal("1000.00")
    return account


class TestAccountServiceCreate:
    @pytest.mark.asyncio
    async def test_account_service_create_account_success(
        self, account_repository_mock, finance, account
    ):
        payload = PayloadAccountCreateSchema(
            name="Test Account",
            type=AccountTypeEnum.BANK,
            initial_balance=1000.00,
        )
        expected = SimpleNamespace(
            id=uuid4(),
            name=payload.name,
            type=payload.type,
            is_active=True,
            initial_balance=payload.initial_balance,
            current_balance=0,
        )
        account_repository_mock.save.return_value = expected
        service = AccountService(repository=account_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)

        result = await service.create(finance=finance, payload=payload)
        assert result == expected
        account_repository_mock.save.assert_awaited_once()
        saved_entity = account_repository_mock.save.await_args.kwargs["entity"]
        assert saved_entity.name == expected.name
        assert saved_entity.type == expected.type
        assert saved_entity.is_active == expected.is_active
        assert saved_entity.initial_balance == expected.initial_balance
        assert saved_entity.current_balance == expected.current_balance


class TestAccountServicePersist:
    @pytest.mark.asyncio
    async def test_account_service_persist_existing_account_with_throw(
        self, account_service, finance, account
    ):
        with patch.object(
            account_service, "find_by", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = account
            with pytest.raises(HTTPException) as exc_info:
                await account_service.persist(
                    name="Test Account",
                    type=AccountTypeEnum.BANK,
                    finance=finance,
                    initial_balance=1000.00,
                    with_throw=True,
                )

            assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
            assert "already exists" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_account_service_persist_existing_account_without_throw(
        self, account_service, finance, account
    ):
        with patch.object(
            account_service, "find_by", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = account
            result = await account_service.persist(
                name="Test Account",
                type=AccountTypeEnum.BANK,
                finance=finance,
                initial_balance=1000.00,
                with_throw=False,
            )

            assert result.id == "test-account-id"

    @pytest.mark.asyncio
    async def test_account_service_persist_new_account(
        self, account_service, finance, account
    ):
        with patch.object(
            account_service, "find_by", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = None
            with patch.object(
                account_service.repository, "save", new_callable=AsyncMock
            ) as mock_save:
                mock_save.return_value = account
                account_service.cache_service.delete_with_parent_cache = AsyncMock(
                    return_value=None
                )
                result = await account_service.persist(
                    name="Test Account",
                    type=AccountTypeEnum.BANK,
                    finance=finance,
                    initial_balance=1000.00,
                )

                assert result.id == "test-account-id"
                mock_save.assert_called_once()


class TestAccountServiceRecalculate:
    @pytest.mark.asyncio
    async def test_account_service_recalculate_balance_with_income(
        self, account_service, finance
    ):
        account_with_income = MagicMock(spec=Account)
        account_with_income.id = "test-account-id"
        account_with_income.finance_id = "test-finance-id"
        account_with_income.name = "Test Account"
        account_with_income.current_balance = Decimal("1000.00")
        account_with_income.incomes = [MagicMock(amount=Decimal("500.00"))]
        account_with_income.incoming_transfers = []
        account_with_income.outgoing_transfers = []
        account_with_income.expenses = []
        account_with_income.initial_balance = Decimal("1000.00")

        with patch.object(
            account_service, "find_one", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = account_with_income
            with patch.object(
                account_service, "update_entity", new_callable=AsyncMock
            ) as mock_update:
                mock_update.return_value = account_with_income
                account_service.cache_service.delete_with_parent_cache = AsyncMock(
                    return_value=None
                )
                result = await account_service.recalculate(
                    param="test-account-id", finance=finance
                )

                assert result.current_balance == Decimal("1500.00")
                mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_account_service_recalculate_balance_no_changes(
        self, account_service, finance
    ):
        account_no_changes = MagicMock(spec=Account)
        account_no_changes.id = "test-account-id"
        account_no_changes.finance_id = "test-finance-id"
        account_no_changes.name = "Test Account"
        account_no_changes.current_balance = Decimal("1000.00")
        account_no_changes.incomes = []
        account_no_changes.incoming_transfers = []
        account_no_changes.outgoing_transfers = []
        account_no_changes.expenses = []
        account_no_changes.initial_balance = Decimal("1000.00")

        with patch.object(
            account_service, "find_one", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = account_no_changes
            result = await account_service.recalculate(
                param="test-account-id", finance=finance
            )

            assert result.current_balance == Decimal("1000.00")
