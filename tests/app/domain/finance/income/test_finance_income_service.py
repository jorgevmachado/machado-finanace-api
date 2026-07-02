from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from http import HTTPStatus

from app.domain.finance.income.service import IncomeService
from app.domain.finance.income.schema import PayloadIncomeCreateSchema


@pytest.fixture
def income_repository_mock():
    return AsyncMock()


@pytest.fixture
def account_service_mock():
    return AsyncMock()


@pytest.fixture
def income_month_service_mock():
    return AsyncMock()


class TestFinanceIncomeService:
    @staticmethod
    def test_from_session_builds_service(income_repository_mock: AsyncMock):
        service = IncomeService(repository=income_repository_mock)
        assert isinstance(service, IncomeService)
        assert service.repository is income_repository_mock

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
        income_repository_mock, account_service_mock, income_month_service_mock
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
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

        result = await service.create(finance=finance, payload=payload)

        assert result is expected_income
        account_service_mock.find_by.assert_awaited_once()
        income_repository_mock.save.assert_awaited_once()
        income_month_service_mock.persist_list.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_with_existing_income_throws(
        income_repository_mock, account_service_mock, income_month_service_mock
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
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

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_by_account_empty_list(
        income_repository_mock, account_service_mock, income_month_service_mock
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())

        service = IncomeService(
            repository=income_repository_mock,
            account_service=account_service_mock,
            income_month_service=income_month_service_mock,
        )

        result = await service.create_by_account(
            finance=finance,
            account=account,
            reference_day=10,
            reference_year=2026,
            payload_incomes=[],
        )

        assert result == []
        income_repository_mock.save.assert_not_awaited()

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_with_existing_income_no_throw_updates(
        income_repository_mock, account_service_mock, income_month_service_mock
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        existing_income = SimpleNamespace(
            id=uuid4(), 
            source="Test Income",
            description="Old Description"
        )
        updated_income = SimpleNamespace(
            id=existing_income.id,
            source="Test Income", 
            description="New Description"
        )

        payload = PayloadIncomeCreateSchema(
            months=[],
            source="Test Income",
            account_id=account.id,
            description="New Description",
            reference_year=2026,
        )

        income_repository_mock.find_by.return_value = existing_income
        income_repository_mock.update.return_value = updated_income
        income_month_service_mock.persist_list.return_value = []

        service = IncomeService(
            repository=income_repository_mock,
            account_service=account_service_mock,
            income_month_service=income_month_service_mock,
        )

        result = await service._persist(
            payload=payload,
            account=account,
            finance=finance,
            with_throw=False,
        )

        assert result == updated_income
        assert result.description == "New Description"
        income_repository_mock.update.assert_awaited_once()
        income_month_service_mock.persist_list.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_by_account_with_single_payload_income(
        income_repository_mock, account_service_mock, income_month_service_mock
    ):
        from app.domain.finance.schema import FinanceCreateIncomeSchema
        from app.domain.finance.expense_month.schema import PayloadExpenseMonthPersistSchema
        
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        created_income = SimpleNamespace(id=uuid4(), source="Salary")

        payload_incomes = [
            FinanceCreateIncomeSchema(
                source="Salary",
                description="Monthly Salary",
                months=[
                    PayloadExpenseMonthPersistSchema(
                        amount=5000,
                        reference_month=1,
                    )
                ],
            )
        ]

        income_repository_mock.find_by.side_effect = [None, created_income]
        income_repository_mock.save.return_value = created_income
        income_month_service_mock.persist_list.return_value = []

        service = IncomeService(
            repository=income_repository_mock,
            account_service=account_service_mock,
            income_month_service=income_month_service_mock,
        )

        result = await service.create_by_account(
            finance=finance,
            account=account,
            reference_day=10,
            reference_year=2026,
            payload_incomes=payload_incomes,
        )

        assert len(result) == 1
        assert result[0] == created_income

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_by_account_with_multiple_payloads(
        income_repository_mock, account_service_mock, income_month_service_mock
    ):
        from app.domain.finance.schema import FinanceCreateIncomeSchema
        from app.domain.finance.expense_month.schema import PayloadExpenseMonthPersistSchema
        
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        income1 = SimpleNamespace(id=uuid4(), source="Salary")
        income2 = SimpleNamespace(id=uuid4(), source="Bonus")

        payload_incomes = [
            FinanceCreateIncomeSchema(
                source="Salary",
                description="Monthly Salary",
                months=[
                    PayloadExpenseMonthPersistSchema(
                        amount=5000,
                        reference_month=1,
                    ),
                    PayloadExpenseMonthPersistSchema(
                        amount=5000,
                        reference_month=2,
                    )
                ],
            ),
            FinanceCreateIncomeSchema(
                source="Bonus",
                description="Annual Bonus",
                months=[
                    PayloadExpenseMonthPersistSchema(
                        amount=2000,
                        reference_month=12,
                    )
                ],
            ),
        ]

        income_repository_mock.find_by.side_effect = [None, income1, None, income2]
        income_repository_mock.save.side_effect = [income1, income2]
        income_month_service_mock.persist_list.return_value = []

        service = IncomeService(
            repository=income_repository_mock,
            account_service=account_service_mock,
            income_month_service=income_month_service_mock,
        )

        result = await service.create_by_account(
            finance=finance,
            account=account,
            reference_day=10,
            reference_year=2026,
            payload_incomes=payload_incomes,
        )

        assert len(result) == 2
        assert result[0] == income1
        assert result[1] == income2
        assert income_repository_mock.save.await_count == 2

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_by_account_with_no_months_in_payload(
        income_repository_mock, account_service_mock, income_month_service_mock
    ):
        from app.domain.finance.schema import FinanceCreateIncomeSchema
        
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        created_income = SimpleNamespace(id=uuid4(), source="Freelance")

        payload_incomes = [
            FinanceCreateIncomeSchema(
                source="Freelance",
                description=None,
                months=[],
            )
        ]

        income_repository_mock.find_by.side_effect = [None, created_income]
        income_repository_mock.save.return_value = created_income
        income_month_service_mock.persist_list.return_value = []

        service = IncomeService(
            repository=income_repository_mock,
            account_service=account_service_mock,
            income_month_service=income_month_service_mock,
        )

        result = await service.create_by_account(
            finance=finance,
            account=account,
            reference_day=10,
            reference_year=2026,
            payload_incomes=payload_incomes,
        )

        assert len(result) == 1
        assert result[0] == created_income


