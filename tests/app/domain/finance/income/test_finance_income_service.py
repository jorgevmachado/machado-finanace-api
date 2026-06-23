from __future__ import annotations

from http import HTTPStatus
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4


import pytest
from fastapi import HTTPException

from app.domain.finance.income.schema import (
    PayloadIncomeCreateSchema,
    PayloadIncomeCreateListItemSchema,
    PayloadIncomeCreateListSchema,
)
from app.domain.finance.income.service import IncomeService
from app.models import utcnow
from app.shared.utils.string import to_snake_case


@pytest.fixture
def income_repository_mock() -> AsyncMock:
    return AsyncMock()

@pytest.fixture
def payload_income_create_list_item():
    return PayloadIncomeCreateListItemSchema(amount=100, reference_month=1)

@pytest.fixture
def payload_income_create_list( payload_income_create_list_item):
    payload_income_create_list_item_1 = payload_income_create_list_item    
    payload_income_create_list_item_2 = payload_income_create_list_item
    payload_income_create_list_item_2.reference_month = 2
    payload_income_create_list_item_3 = payload_income_create_list_item
    payload_income_create_list_item_3.reference_month = 3
    return PayloadIncomeCreateListSchema(
    account_id=uuid4(),
    source="Test Income",
    reference_day=5,
    reference_year=2026,
    description="Some Description",
    incomes=[
        payload_income_create_list_item_1,
        payload_income_create_list_item_2,
        payload_income_create_list_item_3
    ],
)


class TestFinanceIncomeServiceFromSession:
    @staticmethod
    @pytest.mark.asyncio
    async def test_from_session_builds_service() -> None:
        service = IncomeService.from_session(AsyncMock())
        assert isinstance(service, IncomeService)


class TestFinanceIncomeCreateService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_service_create_not_has_finance(
        income_repository_mock: AsyncMock,
    ):

        payload = PayloadIncomeCreateSchema(
            source="Test Income",
            amount=100.0,
            account_id=uuid4(),
            received_at=date(2023, 1, 1),
            description="Some Description",
            reference_year=2023,
            reference_month=1,
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=None
        )

        service = IncomeService(repository=income_repository_mock)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "User must be onboarded first"

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
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = IncomeService(repository=income_repository_mock)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

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
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = IncomeService(repository=income_repository_mock)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

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
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = IncomeService(repository=income_repository_mock)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

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
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = IncomeService(repository=income_repository_mock)
        service.find_by = AsyncMock(return_value=SimpleNamespace(id=uuid4()))
        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

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
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = IncomeService(repository=income_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        service.account_service.find_by = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

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
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = IncomeService(repository=income_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        service.account_service.find_by = AsyncMock(
            return_value=SimpleNamespace(id=account_id)
        )
        income_repository_mock.save.return_value = expected

        result = await service.create(current_user=current_user, payload=payload)

        assert result == expected

class TestFinanceIncomeCreateListService:
        
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_service_create_list_not_has_finance(
        income_repository_mock: AsyncMock,
        payload_income_create_list: PayloadIncomeCreateListSchema
    ):

        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=None
        )

        service = IncomeService(repository=income_repository_mock)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_list_by_year(current_user=current_user, payload=payload_income_create_list)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "User must be onboarded first"

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_service_create_list_empty_incomes(
        income_repository_mock: AsyncMock,
        payload_income_create_list: PayloadIncomeCreateListSchema,
    ):
        payload = payload_income_create_list
        payload.incomes = []
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = IncomeService(repository=income_repository_mock)
        service.account_service.find_by = AsyncMock(return_value=SimpleNamespace(id=payload.account_id))

        with pytest.raises(HTTPException) as exc_info:
            await service.create_list_by_year(
                current_user=current_user, payload=payload_income_create_list
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "Incomes must be between 1 and 12"

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_income_service_create_list_successfully(
        income_repository_mock: AsyncMock,
        payload_income_create_list: PayloadIncomeCreateListSchema,
    ):
        payload = payload_income_create_list
        payload.incomes = payload.incomes[0:1]

        expected: list[SimpleNamespace] = []
        for item in payload.incomes:
            reference_day = payload.reference_day or 1
            income = SimpleNamespace(
                id=uuid4(),
                source=payload.source,
                amount=item.amount,
                source_code=to_snake_case(payload.source),
                account_id=payload.account_id,
                received_at=date(payload.reference_year, item.reference_month, reference_day),
                description=payload.description,
                reference_year=payload.reference_year,
                reference_month=item.reference_month,
            )
            expected.append(income)


        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = IncomeService(repository=income_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        service.account_service.find_by = AsyncMock(
            return_value=SimpleNamespace(id=payload.account_id)
        )
        for item in expected:
            service._persist = AsyncMock(return_value=item)

        result = await service.create_list_by_year(current_user=current_user, payload=payload)

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

        result = await service._persist(payload=payload, finance=finance, account=account, with_throw=False)

        assert result == expected

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