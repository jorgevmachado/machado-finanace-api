from __future__ import annotations

from http import HTTPStatus
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4


import pytest
from fastapi import HTTPException

from app.domain.finance.income.schema import (
    PayloadIncomeCreateSchema
)
from app.domain.finance.schema import FinanceCreateIncomeSchema, FinanceCreateMonthSchema
from app.domain.finance.income.service import IncomeService
from app.models import utcnow


@pytest.fixture
def income_repository_mock() -> AsyncMock:
    return AsyncMock()

class TestFinanceIncomeServiceFromSession:
    @staticmethod
    @pytest.mark.asyncio
    async def test_from_session_builds_service() -> None:
        service = IncomeService.from_session(AsyncMock())
        assert isinstance(service, IncomeService)

class TestFinanceIncomeCreateService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_service_create_invalid_year(
        income_repository_mock: AsyncMock,
    ):
        current_year = utcnow().year
        year = current_year + 1
        payload = PayloadIncomeCreateSchema(
            source="Test Income",
            amount=100.0,
            account_id=uuid4(),
            received_at=date(2023, 1, 1),
            description="Some Description",
            reference_year=year,
            reference_month=1,
        )
        finance = SimpleNamespace(
            id=uuid4()
        )

        service = IncomeService(repository=income_repository_mock)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Reference year {year} must be less than or equal to the current year {current_year}"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_service_create_month_less_than_1(
        income_repository_mock: AsyncMock,
    ):
        month = 0
        payload = PayloadIncomeCreateSchema(
            source="Test Income",
            amount=100.0,
            account_id=uuid4(),
            received_at=date(2023, 1, 1),
            description="Some Description",
            reference_year=utcnow().year,
            reference_month=month,
        )
        finance = SimpleNamespace(id=uuid4())

        service = IncomeService(repository=income_repository_mock)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail == f"Reference month {month} must be between 1 and 12"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_service_create_month_bigger_than_12(
        income_repository_mock: AsyncMock,
    ):
        month = 13
        payload = PayloadIncomeCreateSchema(
            source="Test Income",
            amount=100.0,
            account_id=uuid4(),
            received_at=date(2023, 1, 1),
            description="Some Description",
            reference_year=utcnow().year,
            reference_month=month,
        )
        finance = SimpleNamespace(id=uuid4())

        service = IncomeService(repository=income_repository_mock)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail == f"Reference month {month} must be between 1 and 12"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_service_create_exist(
        income_repository_mock: AsyncMock,
    ):
        payload = PayloadIncomeCreateSchema(
            source="Test Income",
            amount=100.0,
            account_id=uuid4(),
            received_at=date(2023, 1, 1),
            description="Some Description",
            reference_year=utcnow().year,
            reference_month=1,
        )
        finance = SimpleNamespace(id=uuid4())

        service = IncomeService(repository=income_repository_mock)
        service.find_by = AsyncMock(return_value=SimpleNamespace(id=uuid4()))
        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Income with this year {payload.reference_year}, month {payload.reference_month} and source {payload.source} already exists"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_service_create_account_not_exist(
        income_repository_mock: AsyncMock,
    ):
        payload = PayloadIncomeCreateSchema(
            source="Test Income",
            amount=100.0,
            account_id=uuid4(),
            received_at=date(2023, 1, 1),
            description="Some Description",
            reference_year=utcnow().year,
            reference_month=1,
        )
        finance = SimpleNamespace(id=uuid4())

        service = IncomeService(repository=income_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        service.account_service.find_by = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Account with this id {payload.account_id} does not exist"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_service_create_successfully(
        income_repository_mock: AsyncMock,
    ):
        account_id = uuid4()
        current_year = utcnow().year
        current_month = 1
        payload = PayloadIncomeCreateSchema(
            source="Test Income",
            amount=100.0,
            account_id=account_id,
            received_at=date(current_year, current_month, 1),
            description="Some Description",
            reference_year=utcnow().year,
            reference_month=1,
        )
        expected = SimpleNamespace(
            id=uuid4(),
            source=payload.source,
            amount=payload.amount,
            source_code="test_income",
            account_id=payload.account_id,
            received_at=payload.received_at,
            description=payload.description,
            reference_year=payload.reference_year,
            reference_month=payload.reference_month,
        )
        finance = SimpleNamespace(id=uuid4())

        service = IncomeService(repository=income_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        service.account_service.find_by = AsyncMock(
            return_value=SimpleNamespace(id=account_id)
        )
        income_repository_mock.save.return_value = expected

        result = await service.create(finance=finance, payload=payload)

        assert result == expected

class TestFinanceIncomePersistService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_service_persist_update_successfully(
        income_repository_mock: AsyncMock,
    ):
        account_id = uuid4()
        current_year = utcnow().year
        current_month = 1
        payload = PayloadIncomeCreateSchema(
            source="Test Income",
            amount=100.0,
            account_id=account_id,
            received_at=date(current_year, current_month, 1),
            description="Some Description",
            reference_year=utcnow().year,
            reference_month=1,
        )
        expected = SimpleNamespace(
            id=uuid4(),
            source=payload.source,
            amount=payload.amount,
            source_code="test_income",
            account_id=payload.account_id,
            received_at=payload.received_at,
            description=payload.description,
            reference_year=payload.reference_year,
            reference_month=payload.reference_month,
        )

        finance = SimpleNamespace(id=uuid4())

        account = SimpleNamespace(id=account_id)

        service = IncomeService(repository=income_repository_mock)
        service.find_by = AsyncMock(return_value=expected)
        income_repository_mock.update.return_value = expected

        result = await service._persist(
            payload=payload, finance=finance, account=account, with_throw=False
        )

        assert result == expected

class TestFinanceIncomeCreateByAccountService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_service_create_by_account_merge_months(
        income_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())

        payload_incomes = [
            FinanceCreateIncomeSchema(
                source="Salario",
                months=[
                    FinanceCreateMonthSchema(
                        amount=100.0,
                        reference_month=1,
                    ),
                    FinanceCreateMonthSchema(
                        amount=200.0,
                        reference_month=1,
                    ),
                    FinanceCreateMonthSchema(
                        amount=50.0,
                        reference_day=12,
                        reference_month=2,
                    ),
                ],
                description="Receita",
            )
        ]

        service = IncomeService(repository=income_repository_mock)
        service._persist = AsyncMock(return_value=SimpleNamespace(id=uuid4()))

        await service.create_by_account(
            finance=finance,
            account=account,
            reference_day=5,
            reference_year=utcnow().year,
            payload_incomes=payload_incomes,
        )

        assert service._persist.await_count == 2

        first_payload = service._persist.await_args_list[0].kwargs["payload"]
        second_payload = service._persist.await_args_list[1].kwargs["payload"]

        assert first_payload.reference_month == 1
        assert first_payload.amount == 300.0
        assert second_payload.reference_month == 2
        assert second_payload.amount == 50.0

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_service_persist_create_successfully(
        income_repository_mock: AsyncMock,
    ):
        account_id = uuid4()
        current_year = utcnow().year
        current_month = 1
        payload = PayloadIncomeCreateSchema(
            source="Test Income",
            amount=100.0,
            account_id=account_id,
            received_at=date(current_year, current_month, 1),
            description="Some Description",
            reference_year=utcnow().year,
            reference_month=1,
        )
        expected = SimpleNamespace(
            id=uuid4(),
            source=payload.source,
            amount=payload.amount,
            source_code="test_income",
            account_id=payload.account_id,
            received_at=payload.received_at,
            description=payload.description,
            reference_year=payload.reference_year,
            reference_month=payload.reference_month,
        )

        finance = SimpleNamespace(id=uuid4())

        account = SimpleNamespace(id=account_id)

        service = IncomeService(repository=income_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        income_repository_mock.save.return_value = expected

        result = await service._persist(
            payload=payload, finance=finance, account=account, with_throw=False
        )

        assert result == expected
