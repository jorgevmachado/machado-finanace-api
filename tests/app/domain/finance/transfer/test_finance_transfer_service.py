from __future__ import annotations

from datetime import date
from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4


import pytest
from fastapi import HTTPException

from app.domain.finance.transfer.schema import (
    PayloadTransferCreateSchema,
)
from app.domain.finance.transfer.service import (
    TransferService,
)
from app.models import utcnow

@pytest.fixture
def transfer_repository_mock() -> AsyncMock:
    return AsyncMock()

class TestFinanceTransferServiceFromSession:
    @staticmethod
    @pytest.mark.asyncio
    async def test_from_session_builds_service() -> None:
        service = TransferService.from_session(AsyncMock())
        assert isinstance(service, TransferService)
        
class TestFinanceTransferCreateService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_transfer_service_create_exist(
        transfer_repository_mock: AsyncMock,
    ):
        current_date = utcnow()
        payload = PayloadTransferCreateSchema(
            amount=150.0,
            to_account_id=uuid4(),
            transfer_date=date(current_date.year, current_date.month, 1),
            from_account_id=uuid4(),
            description="Some Description",
        )
        finance = SimpleNamespace(id=uuid4())

        service = TransferService(repository=transfer_repository_mock)
        service.find_by = AsyncMock(return_value=SimpleNamespace(id=uuid4()))
        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "Transfer already exists"

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_transfer_service_create_to_account_not_exist(
        transfer_repository_mock: AsyncMock,
    ):
        current_date = utcnow()
        payload = PayloadTransferCreateSchema(
            amount=150.0,
            to_account_id=uuid4(),
            transfer_date=date(current_date.year, current_date.month, 1),
            from_account_id=uuid4(),
            description="Some Description",
        )
        finance = SimpleNamespace(id=uuid4())

        service = TransferService(repository=transfer_repository_mock)
        service.find_by = AsyncMock(return_value=None)

        service.account_service.find_by = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == f"To Account with this id {payload.to_account_id} does not exist"

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_transfer_service_create_from_account_not_exist(
        transfer_repository_mock: AsyncMock,
    ):
        current_date = utcnow()
        payload = PayloadTransferCreateSchema(
            amount=150.0,
            to_account_id=uuid4(),
            transfer_date=date(current_date.year, current_date.month, 1),
            from_account_id=uuid4(),
            description="Some Description",
        )
        finance = SimpleNamespace(id=uuid4())

        service = TransferService(repository=transfer_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        service.account_service.find_by = AsyncMock(
            side_effect=[
                SimpleNamespace(id=payload.to_account_id),
                None,
            ]
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"From Account with this id {payload.from_account_id} does not exist"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_transfer_service_create_successfully(
        transfer_repository_mock: AsyncMock,
    ):
        current_date = utcnow()
        payload = PayloadTransferCreateSchema(
            amount=150.0,
            to_account_id=uuid4(),
            transfer_date=date(current_date.year, current_date.month, 1),
            from_account_id=uuid4(),
            description="Some Description",
        )
        expected = SimpleNamespace(
            id=uuid4(),
            amount=payload.amount,
            to_account_id=payload.to_account_id,
            transfer_date=payload.transfer_date,
            from_account_id=payload.from_account_id,
            description=payload.description,
        )
        finance = SimpleNamespace(id=uuid4())

        service = TransferService(repository=transfer_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        service.account_service.find_by = AsyncMock(
            side_effect=[
                SimpleNamespace(id=payload.to_account_id),
                SimpleNamespace(id=payload.from_account_id),
            ]
        )
        service.repository.save.return_value = expected
        result = await service.create(finance=finance, payload=payload)
        assert result == expected

class TestFinanceTransfer_PesistService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_transfer_persist_updates_existing_transfer(
        transfer_repository_mock: AsyncMock,
    ):
        """Test _persist when transfer already exists (with_throw=False)"""
        current_date = utcnow()

        finance = SimpleNamespace(id=uuid4())
        to_account = SimpleNamespace(id=uuid4())
        from_account = SimpleNamespace(id=uuid4())        

        payload = PayloadTransferCreateSchema(
            amount=150.0,
            to_account_id=to_account.id,
            transfer_date=date(current_date.year, current_date.month, 1),
            from_account_id=from_account.id,
            description="Some Description",
        )

        existing_transfer = SimpleNamespace(
            id=uuid4(),
            amount=payload.amount,
            to_account_id=payload.to_account_id,
            transfer_date=payload.transfer_date,
            from_account_id=payload.from_account_id,
            description=payload.description,
        )

        service = TransferService(repository=transfer_repository_mock)
        service.find_by = AsyncMock(return_value=existing_transfer)
        transfer_repository_mock.update.return_value = existing_transfer

        result = await service._persist(
            finance=finance,
            to_account=to_account,
            from_account=from_account,
            payload=payload,
            with_throw=False,
        )

        # Verify that update was called (not save)
        transfer_repository_mock.update.assert_awaited_once()
        transfer_repository_mock.save.assert_not_awaited()
        assert result == existing_transfer

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_transfer_persist_creates_separate_transfers_for_different_transfer_dates(
        transfer_repository_mock: AsyncMock,
    ):
        """Test _persist when transfer already exists (with_throw=False)"""
        current_date = utcnow()

        finance = SimpleNamespace(id=uuid4())
        to_account = SimpleNamespace(id=uuid4())
        from_account = SimpleNamespace(id=uuid4())

        payload_jan = PayloadTransferCreateSchema(
            amount=150.0,
            to_account_id=to_account.id,
            transfer_date=date(current_date.year, 1, 1),
            from_account_id=from_account.id,
            description="January Transfer",
        )

        payload_feb = PayloadTransferCreateSchema(
            amount=200.0,
            to_account_id=to_account.id,
            transfer_date=date(current_date.year, 2, 1),
            from_account_id=from_account.id,
            description="February Transfer",
        )

        service = TransferService(repository=transfer_repository_mock)
        service.find_by = AsyncMock(return_value=None)

        # Mock save to return expense as-is
        def save_side_effect(entity):
            return entity
                    
        transfer_repository_mock.save.side_effect = save_side_effect

        result_jan = await service._persist(
            finance=finance,
            to_account=to_account,
            from_account=from_account,
            payload=payload_jan,
            with_throw=False,
        )

        result_feb = await service._persist(
            finance=finance,
            to_account=to_account,
            from_account=from_account,
            payload=payload_feb,
            with_throw=False,
        )

        assert service.find_by.await_count == 2

        first_call_kwargs = service.find_by.call_args_list[0][1]
        assert first_call_kwargs["finance_id"] == finance.id
        assert first_call_kwargs["to_account_id"] == to_account.id
        assert first_call_kwargs["from_account_id"] == from_account.id
        assert first_call_kwargs["transfer_date"] == payload_jan.transfer_date

        second_call_kwargs = service.find_by.call_args_list[1][1]
        assert second_call_kwargs["finance_id"] == finance.id
        assert second_call_kwargs["to_account_id"] == to_account.id
        assert second_call_kwargs["from_account_id"] == from_account.id
        assert second_call_kwargs["transfer_date"] == payload_feb.transfer_date

        assert result_jan.description == payload_jan.description
        assert result_feb.description == payload_feb.description
        assert result_jan.description != result_feb.description