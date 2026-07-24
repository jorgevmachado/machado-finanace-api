from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from http import HTTPStatus

from app.domain.finance.income.service import IncomeService
from app.domain.finance.income.schema import (
    PayloadIncomeCreateSchema,
    PayloadIncomePersistSchema,
    PayloadIncomeUpdateSchema,
)
from app.domain.finance.months.schema import PayloadMonthPersistSchema
from app.models import utcnow, Account, Income


@pytest.fixture
def income_repository_mock():
    return AsyncMock()


@pytest.fixture
def account_service_mock():
    return AsyncMock()


@pytest.fixture
def income_month_service_mock():
    return AsyncMock()


@pytest.fixture
def account():
    account = MagicMock(spec=Account)
    account.id = uuid4()
    account.finance_id = uuid4()
    return account


@pytest.fixture()
def income():
    income = MagicMock(spec=Income)
    income.id = uuid4()
    income.months = []
    income.source = "Test Income"
    income.description = "Test Income Description"
    return income


@pytest.fixture
def payload_months(value: float = 100.0):
    months: list[PayloadMonthPersistSchema] = []
    for i in range(1, 13):
        months.append(PayloadMonthPersistSchema(amount=value, reference_month=i))
    return months

class TestFinanceIncomeFromSessionService:
    @staticmethod
    def test_from_session_builds_service(income_repository_mock: AsyncMock):
        service = IncomeService(repository=income_repository_mock)
        assert isinstance(service, IncomeService)
        assert service.repository is income_repository_mock

class TestFinanceIncomeFindByService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_find_by_success(income_repository_mock, account_service_mock):
        expected_income = SimpleNamespace(id=uuid4(), source="Test Income")
        income_repository_mock.find_by.return_value = expected_income

        service = IncomeService(
            repository=income_repository_mock,
            account_service=account_service_mock,
        )
        result = await service.find_by(id=expected_income.id)

        assert result is expected_income
        income_repository_mock.find_by.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_find_by_not_found(income_repository_mock, account_service_mock):
        income_repository_mock.find_by.return_value = None

        service = IncomeService(
            repository=income_repository_mock,
            account_service=account_service_mock,
        )
        result = await service.find_by(id=uuid4(), without_throw=True)

        assert result is None

class TestFinanceIncomeCreateService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_create_validates_account_not_found(
        income_repository_mock, account_service_mock, income_month_service_mock
    ):
        finance = SimpleNamespace(id=uuid4())
        account_id = uuid4()
        payload = PayloadIncomeCreateSchema(
            months=[],
            source="Test Income",
            account_id=account_id,
            description="Test Description",
            reference_year=2026,
        )

        account_service_mock.find_by.return_value = None

        service = IncomeService(
            repository=income_repository_mock,
            account_service=account_service_mock,
            income_month_service=income_month_service_mock,
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        account_service_mock.find_by.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_with_valid_account_new_income(
        income_repository_mock, account_service_mock, income_month_service_mock, account
    ):
        finance = SimpleNamespace(id=uuid4())
        account_id = account.id
        payload = PayloadIncomeCreateSchema(
            months=[],
            source="Test Income",
            account_id=account_id,
            description="Test Description",
            reference_year=2026,
        )

        expected_income = SimpleNamespace(id=uuid4(), source=payload.source)
        account_service_mock.find_by.return_value = account
        income_repository_mock.find_by.side_effect = [None, expected_income]
        income_repository_mock.save.return_value = expected_income

        service = IncomeService(
            repository=income_repository_mock,
            account_service=account_service_mock,
            income_month_service=income_month_service_mock,
        )
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
        result = await service.create(finance=finance, payload=payload)

        assert result is expected_income
        account_service_mock.find_by.assert_awaited_once()
        income_repository_mock.save.assert_awaited_once()
        income_month_service_mock.persist_list.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_with_existing_income_throws(
        income_repository_mock, account_service_mock, income_month_service_mock, account
    ):
        finance = SimpleNamespace(id=uuid4())
        existing_income = SimpleNamespace(id=uuid4(), source="Test Income")
        payload = PayloadIncomeCreateSchema(
            months=[],
            source="Test Income",
            account_id=account.id,
            description="Test Description",
            reference_year=2026,
        )

        account_service_mock.find_by.return_value = account
        income_repository_mock.find_by.return_value = existing_income

        service = IncomeService(
            repository=income_repository_mock,
            account_service=account_service_mock,
            income_month_service=income_month_service_mock,
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST

class TestFinanceIncomePersistService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_persist_service_invalid_year(
        income_repository_mock, account
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
        source = "Some Source"
        description = "Some Description"
        current_year = utcnow().year
        reference_day = 10
        reference_year = current_year + 1

        service = IncomeService(repository=income_repository_mock)
        with pytest.raises(HTTPException) as exc_info:
            await service.persist(
                months=months,
                source=source,
                account=account,
                with_throw=True,
                description=description,
                reference_day=reference_day,
                reference_year=reference_year,
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Reference year {reference_year} must be less than or equal to the current year {current_year}"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_persist_service_exist_income_with_throw(
        income_repository_mock, account
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
        source = "Some Source"
        description = "Some Description"
        current_year = utcnow().year
        reference_day = 10
        reference_year = current_year

        existing_income = SimpleNamespace(
            id=uuid4(), source=source, description=description
        )
        income_repository_mock.find_by.return_value = existing_income
        service = IncomeService(repository=income_repository_mock)
        with pytest.raises(HTTPException) as exc_info:
            await service.persist(
                months=months,
                source=source,
                account=account,
                with_throw=True,
                description=description,
                reference_day=reference_day,
                reference_year=reference_year,
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Income with this year {reference_year} and source {source} already exists"
        )
        income_repository_mock.find_by.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_persist_service_exist_income_without_throw(
        income_repository_mock, account
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
        source = "Some Source"
        description = "Some Description"
        current_year = utcnow().year
        reference_day = 10
        reference_year = current_year

        existing_income = SimpleNamespace(
            id=uuid4(), source=source, description=description
        )
        income_repository_mock.find_by.return_value = existing_income
        income_repository_mock.update.return_value = existing_income
        service = IncomeService(repository=income_repository_mock)
        service.income_month_service.persist_list = AsyncMock(return_value=months)
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)

        result = await service.persist(
            months=months,
            source=source,
            account=account,
            with_throw=False,
            description=description,
            reference_day=reference_day,
            reference_year=reference_year,
        )
        assert result == existing_income
        income_repository_mock.find_by.assert_awaited_once()
        income_repository_mock.update.assert_awaited_once()
        service.cache_service.delete_with_parent_cache.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_persist_service_save_when_not_exist_income(
        income_repository_mock, account
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
        source = "Some Source"
        description = "Some Description"
        current_year = utcnow().year
        reference_day = 10
        reference_year = current_year

        created_income = SimpleNamespace(
            id=uuid4(), source=source, description=description
        )
        income_repository_mock.save.return_value = created_income
        service = IncomeService(repository=income_repository_mock)
        service.find_by = AsyncMock(side_effect=[None, created_income])
        service.income_month_service.persist_list = AsyncMock(return_value=months)
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)

        result = await service.persist(
            months=months,
            source=source,
            account=account,
            with_throw=False,
            description=description,
            reference_day=reference_day,
            reference_year=reference_year,
        )
        assert result == created_income
        income_repository_mock.save.assert_awaited_once()

class TestFinanceIncomePersistListService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_persist_list_service_successfully(
        income_repository_mock, income, account, payload_months
    ):

        reference_day = 10
        reference_year = utcnow().year

        second_income = income
        second_income.id = uuid4()
        second_income.source = "Second Income"
        second_income.description = "Second Income Description"

        payload_incomes: list[PayloadIncomePersistSchema] = [
            PayloadIncomePersistSchema(
                months=payload_months,
                source=income.source,
                description=income.description,
            ),
            PayloadIncomePersistSchema(
                months=payload_months,
                source=second_income.source,
                description=second_income.description,
            ),
        ]

        service = IncomeService(repository=income_repository_mock)
        service.find_by = AsyncMock(side_effect=[None, income, None, second_income])
        income_repository_mock.save.side_effect = [income, second_income]
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
        result = await service.persist_list(
            account=account,
            payloads=payload_incomes,
            with_throw=False,
            reference_day=reference_day,
            reference_year=reference_year,
        )
        assert len(result) == 2
        assert result[0] == income
        assert result[1] == second_income
        income_repository_mock.save.assert_awaited()
        service.cache_service.delete_with_parent_cache.assert_awaited()

class TestFinanceIncomeUpdateService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_update_service_with_payload_none(
        income_repository_mock, income, account, payload_months
    ):

        payload = PayloadIncomeUpdateSchema(
            months=None,
            source=None,
            account_id=None,
            description=None,
            reference_year=None,
        )

        service = IncomeService(repository=income_repository_mock)
        service.find_one = AsyncMock(return_value=income)


        result = await service.update(
            param=str(income.id),
            payload=payload,
            finance_id=account.finance_id,
            user_request="test_user",
        )
        assert result == income

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_update_service_with_payload_not_changed(
        income_repository_mock, income, account, payload_months
    ):

        income.account = account
        payload = PayloadIncomeUpdateSchema(
            months=income.months,
            source=income.source,
            account_id=income.account.id,
            description=income.description,
            reference_year=None,
        )

        service = IncomeService(repository=income_repository_mock)
        service.find_one = AsyncMock(return_value=income)

        result = await service.update(
            param=str(income.id),
            payload=payload,
            finance_id=account.finance_id,
            user_request="test_user",
        )
        assert result == income

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_update_service_with_payload_account_changed(
        income_repository_mock, income, account, payload_months
    ):
        new_account_id = uuid4()

        income.account = account
        payload = PayloadIncomeUpdateSchema(
            months=income.months,
            source=income.source,
            account_id=new_account_id,
            description=income.description,
            reference_year=None,
        )

        income_expected = income

        service = IncomeService(repository=income_repository_mock)
        service.find_one = AsyncMock(return_value=income)
        service.account_service.find_by = AsyncMock(return_value=account)
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
        income_repository_mock.update.return_value = income_expected

        result = await service.update(
            param=str(income.id),
            payload=payload,
            finance_id=account.finance_id,
            user_request="test_user",
        )
        assert result == income_expected
        income_repository_mock.update.assert_called_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_update_service_with_payload_account_not_found(
        income_repository_mock, income, account, payload_months, account_service_mock
    ):
        new_account_id = uuid4()

        income.account = account
        payload = PayloadIncomeUpdateSchema(
            months=income.months,
            source=income.source,
            account_id=new_account_id,
            description=income.description,
            reference_year=None,
        )

        account_service_mock.find_by.return_value = None
        service = IncomeService(repository=income_repository_mock, account_service=account_service_mock)
        service.find_one = AsyncMock(return_value=income)

        with pytest.raises(HTTPException) as exc_info:
            await service.update(
                param=str(income.id),
                payload=payload,
                finance_id=account.finance_id,
                user_request="test_user",
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        account_service_mock.find_by.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_update_service_with_payload_source_changed(
        income_repository_mock, income, account, payload_months
    ):
        new_source = "New Source"
        income.account = account
        income.source_code = "test_income"
        payload = PayloadIncomeUpdateSchema(
            months=income.months,
            source=new_source,
            account_id=income.account.id,
            description=income.description,
            reference_year=None,
        )

        income_expected = income

        service = IncomeService(repository=income_repository_mock)
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
        service.find_by = AsyncMock(return_value=None)
        service.find_one = AsyncMock(return_value=income)
        income_repository_mock.update.return_value = income_expected

        result = await service.update(
            param=str(income.id),
            payload=payload,
            finance_id=account.finance_id,
            user_request="test_user",
        )
        assert result == income_expected
        income_repository_mock.update.assert_called_once()
        service.cache_service.delete_with_parent_cache.assert_called_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_update_service_with_payload_source_changed_exists(
        income_repository_mock, income, account, payload_months
    ):
        reference_year = utcnow().year
        new_source = "New Source"
        income.account = account
        payload = PayloadIncomeUpdateSchema(
            months=income.months,
            source=new_source,
            account_id=income.account.id,
            description=income.description,
            reference_year=reference_year,
        )

        service = IncomeService(repository=income_repository_mock)
        service.find_by = AsyncMock(return_value=income)
        service.find_one = AsyncMock(return_value=income)

        with pytest.raises(HTTPException) as exc_info:
            await service.update(
                param=str(income.id),
                payload=payload,
                finance_id=account.finance_id,
                user_request="test_user",
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == f"Income with this year {reference_year} and source {payload.source} already exists"

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_update_service_with_payload_description_changed(
        income_repository_mock, income, account, payload_months
    ):

        income.account = account
        payload = PayloadIncomeUpdateSchema(
            months=income.months,
            source=income.source,
            account_id=income.account.id,
            description="New Description",
            reference_year=None,
        )

        income_expected = income

        service = IncomeService(repository=income_repository_mock)
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
        service.find_one = AsyncMock(return_value=income)
        income_repository_mock.update.return_value = income_expected

        result = await service.update(
            param=str(income.id),
            payload=payload,
            finance_id=account.finance_id,
            user_request="test_user",
        )
        assert result == income_expected
        income_repository_mock.update.assert_called_once()
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_update_service_with_payload_months_empty(
        income_repository_mock, income, account
    ):
        income.account = account
        payload = PayloadIncomeUpdateSchema(
            months=[],
            source=income.source,
            account_id=income.account.id,
            description=income.description,
            reference_year=None,
        )

        service = IncomeService(repository=income_repository_mock)
        service.find_one = AsyncMock(return_value=income)

        result = await service.update(
            param=str(income.id),
            payload=payload,
            finance_id=account.finance_id,
            user_request="test_user",
        )
        assert result == income
        income_repository_mock.update.assert_not_called()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_update_service_with_payload_months_changed(
        income_repository_mock, income, account, payload_months, income_month_service_mock
    ):
        income.account = account
        income.months = []
        new_months = payload_months[:3]
        
        payload = PayloadIncomeUpdateSchema(
            months=new_months,
            source=income.source,
            account_id=income.account.id,
            description=income.description,
            reference_year=None,
        )

        income_expected = income
        income_expected.months = new_months

        service = IncomeService(
            repository=income_repository_mock,
            income_month_service=income_month_service_mock
        )
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
        service.find_one = AsyncMock(return_value=income)
        service.cache_service.delete_domain = AsyncMock()
        income_month_service_mock.persist_list = AsyncMock(return_value=new_months)
        income_repository_mock.update.return_value = income_expected

        result = await service.update(
            param=str(income.id),
            payload=payload,
            finance_id=account.finance_id,
            user_request="test_user",
        )
        assert result == income_expected
        income_month_service_mock.persist_list.assert_awaited_once()
        income_repository_mock.update.assert_called_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_update_service_with_payload_account_and_source_changed(
        income_repository_mock, income, account
    ):
        new_account = MagicMock(spec=Account)
        new_account.id = uuid4()
        new_account.finance_id = uuid4()
        new_source = "New Source"

        income.account = account
        income.source_code = "test_income"
        payload = PayloadIncomeUpdateSchema(
            months=income.months,
            source=new_source,
            account_id=new_account.id,
            description=income.description,
            reference_year=None,
        )

        income_expected = income

        service = IncomeService(repository=income_repository_mock)
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
        service.find_one = AsyncMock(return_value=income)
        service.account_service.find_by = AsyncMock(return_value=new_account)
        service.find_by = AsyncMock(return_value=None)
        service.cache_service.delete_domain = AsyncMock()
        income_repository_mock.update.return_value = income_expected

        result = await service.update(
            param=str(income.id),
            payload=payload,
            finance_id=new_account.finance_id,
            user_request="test_user",
        )
        assert result == income_expected
        service.account_service.find_by.assert_awaited_once()
        service.find_by.assert_awaited_once()
        income_repository_mock.update.assert_called_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_update_service_with_payload_reference_year_set(
        income_repository_mock, income, account, income_month_service_mock, payload_months
    ):
        reference_year = 2024
        income.account = account
        income.months = []

        payload = PayloadIncomeUpdateSchema(
            months=payload_months[:2],
            source=income.source,
            account_id=income.account.id,
            description=income.description,
            reference_year=reference_year,
        )

        income_expected = income
        income_expected.months = payload_months[:2]

        service = IncomeService(
            repository=income_repository_mock,
            income_month_service=income_month_service_mock
        )
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
        service.find_one = AsyncMock(return_value=income)
        income_month_service_mock.persist_list = AsyncMock(return_value=payload_months[:2])
        income_repository_mock.update.return_value = income_expected

        result = await service.update(
            param=str(income.id),
            payload=payload,
            finance_id=account.finance_id,
            user_request="test_user",
        )
        
        assert result == income_expected
        call_args = income_month_service_mock.persist_list.call_args
        assert call_args.kwargs["reference_year"] == reference_year
        income_repository_mock.update.assert_called_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_update_service_with_payload_reference_day_set(
        income_repository_mock, income, account, income_month_service_mock, payload_months
    ):
        reference_day = 15
        income.account = account
        income.months = []

        payload = PayloadIncomeUpdateSchema(
            months=payload_months[:2],
            source=income.source,
            account_id=income.account.id,
            description=income.description,
            reference_year=None,
            reference_day=reference_day,
        )

        income_expected = income
        income_expected.months = payload_months[:2]

        service = IncomeService(
            repository=income_repository_mock,
            income_month_service=income_month_service_mock
        )
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
        service.find_one = AsyncMock(return_value=income)
        income_month_service_mock.persist_list = AsyncMock(return_value=payload_months[:2])
        income_repository_mock.update.return_value = income_expected

        result = await service.update(
            param=str(income.id),
            payload=payload,
            finance_id=account.finance_id,
            user_request="test_user",
        )
        
        assert result == income_expected
        call_args = income_month_service_mock.persist_list.call_args
        assert call_args.kwargs["reference_day"] == reference_day
        income_repository_mock.update.assert_called_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_update_service_with_payload_source_and_description_changed(
        income_repository_mock, income, account
    ):
        new_source = "New Source"
        new_description = "New Description"

        income.account = account
        income.source_code = "test_income"
        payload = PayloadIncomeUpdateSchema(
            months=income.months,
            source=new_source,
            account_id=income.account.id,
            description=new_description,
            reference_year=None,
        )

        income_expected = income

        service = IncomeService(repository=income_repository_mock)
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
        service.find_one = AsyncMock(return_value=income)
        service.find_by = AsyncMock(return_value=None)
        income_repository_mock.update.return_value = income_expected

        result = await service.update(
            param=str(income.id),
            payload=payload,
            finance_id=account.finance_id,
            user_request="test_user",
        )
        
        assert result == income_expected
        assert income.source == new_source
        assert income.description == new_description
        income_repository_mock.update.assert_called_once()
