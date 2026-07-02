import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.finance.account.repository import AccountRepository
from app.domain.finance.account.service import AccountService
from app.domain.finance.account.schema import PayloadAccountCreateSchema, PayloadAccountCreateListSchema
from app.models import Account, Finance, AccountTypeEnum


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def account_service(mock_session):
    repository = AccountRepository(mock_session)
    return AccountService(repository)


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
    async def test_create_account_success(self, account_service, finance, account):
        payload = PayloadAccountCreateSchema(
            name="Test Account",
            type=AccountTypeEnum.BANK,
            initial_balance=Decimal("1000.00"),
        )

        with patch.object(account_service, "persist", new_callable=AsyncMock) as mock_persist:
            mock_persist.return_value = account
            result = await account_service.create(finance=finance, payload=payload)

            assert result.id == "test-account-id"
            mock_persist.assert_called_once_with(finance=finance, payload=payload)


class TestAccountServiceCreateList:
    @pytest.mark.asyncio
    async def test_create_list_empty_raises_exception(self, account_service, finance):
        payload = PayloadAccountCreateListSchema(accounts=[])

        with pytest.raises(HTTPException) as exc_info:
            await account_service.create_list(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert "cannot be empty" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_list_success(self, account_service, finance, account):
        payload = PayloadAccountCreateListSchema(
            accounts=[
                PayloadAccountCreateSchema(
                    name="Account 1",
                    type=AccountTypeEnum.BANK,
                    initial_balance=Decimal("1000.00"),
                ),
                PayloadAccountCreateSchema(
                    name="Account 2",
                    type=AccountTypeEnum.CASH,
                    initial_balance=Decimal("500.00"),
                ),
            ]
        )

        with patch.object(account_service, "persist", new_callable=AsyncMock) as mock_persist:
            mock_persist.return_value = account
            result = await account_service.create_list(finance=finance, payload=payload)

            assert len(result) == 2
            assert mock_persist.call_count == 2


class TestAccountServicePersist:
    @pytest.mark.asyncio
    async def test_persist_existing_account_with_throw(self, account_service, finance, account):
        payload = PayloadAccountCreateSchema(
            name="Test Account",
            type=AccountTypeEnum.BANK,
            initial_balance=Decimal("1000.00"),
        )

        with patch.object(account_service, "find_by", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = account
            with pytest.raises(HTTPException) as exc_info:
                await account_service.persist(finance=finance, payload=payload, with_throw=True)

            assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
            assert "already exists" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_persist_existing_account_without_throw(self, account_service, finance, account):
        payload = PayloadAccountCreateSchema(
            name="Test Account",
            type=AccountTypeEnum.BANK,
            initial_balance=Decimal("1000.00"),
        )

        with patch.object(account_service, "find_by", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = account
            result = await account_service.persist(
                finance=finance, payload=payload, with_throw=False
            )

            assert result.id == "test-account-id"

    @pytest.mark.asyncio
    async def test_persist_new_account(self, account_service, finance, account):
        payload = PayloadAccountCreateSchema(
            name="Test Account",
            type=AccountTypeEnum.BANK,
            initial_balance=Decimal("1000.00"),
        )

        with patch.object(account_service, "find_by", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = None
            with patch.object(
                account_service.repository, "save", new_callable=AsyncMock
            ) as mock_save:
                mock_save.return_value = account
                result = await account_service.persist(finance=finance, payload=payload)

                assert result.id == "test-account-id"
                mock_save.assert_called_once()


class TestAccountServiceRecalculate:
    @pytest.mark.asyncio
    async def test_recalculate_balance_with_income(self, account_service, finance):
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

        with patch.object(account_service, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = account_with_income
            with patch.object(account_service, "update_entity", new_callable=AsyncMock) as mock_update:
                mock_update.return_value = account_with_income
                result = await account_service.recalculate(
                    param="test-account-id", finance=finance
                )

                assert result.current_balance == Decimal("1500.00")
                mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_recalculate_balance_no_changes(self, account_service, finance):
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

        with patch.object(account_service, "find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = account_no_changes
            result = await account_service.recalculate(
                param="test-account-id", finance=finance
            )

            assert result.current_balance == Decimal("1000.00")
