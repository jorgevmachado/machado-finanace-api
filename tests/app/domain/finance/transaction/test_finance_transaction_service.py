from __future__ import annotations

from http import HTTPStatus
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4


import pytest
from fastapi import HTTPException

from app.domain.finance.transaction.schema import (
    PayloadTransactionCreateSchema,
)
from app.domain.finance.transaction.service import (
    TransactionService,
)
from app.models import utcnow, TransactionTypeEnum, TransactionStatusEnum


@pytest.fixture
def transaction_repository_mock() -> AsyncMock:
    return AsyncMock()


class TestFinanceTransactionServiceFromSession:
    @staticmethod
    @pytest.mark.asyncio
    async def test_from_session_builds_service() -> None:
        service = TransactionService.from_session(AsyncMock())
        assert isinstance(service, TransactionService)


class TestFinanceAllocationContributionCreateService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_transaction_service_create_not_has_finance(
        transaction_repository_mock: AsyncMock,
    ):
        current_date = utcnow()
        current_year = current_date.year
        payload = PayloadTransactionCreateSchema(
            type=TransactionTypeEnum.EXPENSE,
            amount=150.0,
            status=TransactionStatusEnum.PAID,
            account_id=uuid4(),
            allocation_id=uuid4(),
            category_id=uuid4(),
            description="Some Description",
            transaction_date=date(current_year, 1, 1),
            paid_at=current_date,
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=None
        )

        service = TransactionService(
            repository=transaction_repository_mock
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "User must be onboarded first"
    

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_transaction_service_create_exist(
        transaction_repository_mock: AsyncMock,
    ):
        current_date = utcnow()
        current_year = current_date.year
        payload = PayloadTransactionCreateSchema(
            type=TransactionTypeEnum.EXPENSE,
            amount=150.0,
            status=TransactionStatusEnum.PAID,
            account_id=uuid4(),
            allocation_id=uuid4(),
            category_id=uuid4(),
            description="Some Description",
            transaction_date=date(current_year, 1, 1),
            paid_at=current_date,
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = TransactionService(
            repository=transaction_repository_mock
        )
        service.find_by = AsyncMock(return_value=SimpleNamespace(id=uuid4()))
        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == "Transaction already exists"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_transaction_service_create_account_not_exist(
        transaction_repository_mock: AsyncMock,
    ):
        current_date = utcnow()
        current_year = current_date.year
        payload = PayloadTransactionCreateSchema(
            type=TransactionTypeEnum.EXPENSE,
            amount=150.0,
            status=TransactionStatusEnum.PAID,
            account_id=uuid4(),
            allocation_id=uuid4(),
            category_id=uuid4(),
            description="Some Description",
            transaction_date=date(current_year, 1, 1),
            paid_at=current_date,
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = TransactionService(
            repository=transaction_repository_mock
        )
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
    async def test_finance_transaction_service_create_allocation_not_exist(
        transaction_repository_mock: AsyncMock,
    ):
        current_date = utcnow()
        current_year = current_date.year
        payload = PayloadTransactionCreateSchema(
            type=TransactionTypeEnum.EXPENSE,
            amount=150.0,
            status=TransactionStatusEnum.PAID,
            account_id=uuid4(),
            allocation_id=uuid4(),
            category_id=uuid4(),
            description="Some Description",
            transaction_date=date(current_year, 1, 1),
            paid_at=current_date,
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = TransactionService(
            repository=transaction_repository_mock
        )
        service.find_by = AsyncMock(return_value=None)
        service.account_service.find_by = AsyncMock(
            return_value=SimpleNamespace(id=payload.account_id)
        )
        service.allocation_service.find_by = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Allocation with this id {payload.allocation_id} does not exist"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_transaction_service_create_category_not_exist(
        transaction_repository_mock: AsyncMock,
    ):
        current_date = utcnow()
        current_year = current_date.year
        payload = PayloadTransactionCreateSchema(
            type=TransactionTypeEnum.EXPENSE,
            amount=150.0,
            status=TransactionStatusEnum.PAID,
            account_id=uuid4(),
            allocation_id=uuid4(),
            category_id=uuid4(),
            description="Some Description",
            transaction_date=date(current_year, 1, 1),
            paid_at=current_date,
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = TransactionService(repository=transaction_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        service.account_service.find_by = AsyncMock(
            return_value=SimpleNamespace(id=payload.account_id)
        )
        service.allocation_service.find_by = AsyncMock(return_value=SimpleNamespace(id=payload.allocation_id))
        service.category_service.find_by = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Category with this id {payload.category_id} does not exist"
        )
    
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_allocation_contribution_service_create_successfully(
        transaction_repository_mock: AsyncMock,
    ):
        current_date = utcnow()
        current_year = current_date.year
        payload = PayloadTransactionCreateSchema(
            type=TransactionTypeEnum.EXPENSE,
            amount=150.0,
            status=TransactionStatusEnum.PAID,
            account_id=uuid4(),
            allocation_id=uuid4(),
            category_id=uuid4(),
            description="Some Description",
            transaction_date=date(current_year, 1, 1),
            paid_at=current_date,
        )
        expected = SimpleNamespace(
            id=uuid4(),
            type=payload.type,
            amount=payload.amount,
            status=payload.status,
            account_id=payload.account_id,
            allocation_id=payload.allocation_id,
            category_id=payload.category_id,
            description=payload.description,
            transaction_date=payload.transaction_date,
            paid_at=payload.paid_at,
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = TransactionService(
            repository=transaction_repository_mock
        )
        service.find_by = AsyncMock(return_value=None)
        service.account_service.find_by = AsyncMock(
            return_value=SimpleNamespace(id=payload.account_id)
        )
        service.allocation_service.find_by = AsyncMock(
            return_value=SimpleNamespace(id=payload.allocation_id)
        )
        service.category_service.find_by = AsyncMock(
            return_value=SimpleNamespace(id=payload.category_id)
        )
        service.repository.save.return_value = expected
        result = await service.create(current_user=current_user, payload=payload)
        assert result == expected
