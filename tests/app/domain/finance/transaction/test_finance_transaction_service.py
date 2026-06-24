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
    PayloadTransactionCreateListSchema,
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


class TestFinanceTransactionCreateService:    
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
        finance = SimpleNamespace(
            id=uuid4()
        )

        service = TransactionService(repository=transaction_repository_mock)
        service.find_by = AsyncMock(return_value=SimpleNamespace(id=uuid4()))
        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "Transaction already exists"

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
        finance = SimpleNamespace(id=uuid4())

        service = TransactionService(repository=transaction_repository_mock)
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
        finance = SimpleNamespace(id=uuid4())

        service = TransactionService(repository=transaction_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        service.account_service.find_by = AsyncMock(
            return_value=SimpleNamespace(id=payload.account_id)
        )
        service.allocation_service.find_by = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

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
        finance = SimpleNamespace(id=uuid4())

        service = TransactionService(repository=transaction_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        service.account_service.find_by = AsyncMock(
            return_value=SimpleNamespace(id=payload.account_id)
        )
        service.allocation_service.find_by = AsyncMock(
            return_value=SimpleNamespace(id=payload.allocation_id)
        )
        service.category_service.find_by = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Category {payload.category_id} not found for finance {finance.id}"
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
        finance = SimpleNamespace(id=uuid4())

        service = TransactionService(repository=transaction_repository_mock)
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
        result = await service.create(finance=finance, payload=payload)
        assert result == expected

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_list_successfully(
        transaction_repository_mock: AsyncMock,
    ):
        """Test create_list with valid payload"""
        from app.domain.finance.transaction.schema import (
            PayloadTransactionCreateListCategoryItemSchema,
            PayloadTransactionCreateListItemSchema,
        )
        
        current_date = utcnow()
        current_year = current_date.year
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())
        category = SimpleNamespace(id=uuid4())

        transaction_item = PayloadTransactionCreateListItemSchema(
            reference_month=1,
            amount=100.0,
            status=TransactionStatusEnum.PAID,
        )
        
        category_item = PayloadTransactionCreateListCategoryItemSchema(
            category_id=category.id,
            type=TransactionTypeEnum.EXPENSE,
            description="Test",
            transactions=[transaction_item],
        )
        
        payload = PayloadTransactionCreateListSchema(
            account_id=account.id,
            allocation_id=allocation.id,
            reference_year=current_year,
            categories=[category_item],
        )

        service = TransactionService(repository=transaction_repository_mock)
        service.account_service.find_by = AsyncMock(return_value=account)
        service.allocation_service.find_by = AsyncMock(return_value=allocation)
        service.category_service.find_by = AsyncMock(return_value=category)
        service.find_by = AsyncMock(return_value=None)
        
        def save_side_effect(entity):
            return entity
        
        transaction_repository_mock.save.side_effect = save_side_effect
        
        result = await service.create_list(finance=finance, payload=payload)
        
        assert isinstance(result, list)
        assert len(result) > 0
    @staticmethod
    @pytest.mark.asyncio
    async def test_create_list_empty_categories(
        transaction_repository_mock: AsyncMock,
    ):
        """Test create_list with empty categories list"""
        current_date = utcnow()
        current_year = current_date.year
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())

        payload = PayloadTransactionCreateListSchema(
            account_id=account.id,
            allocation_id=allocation.id,
            reference_year=current_year,
            categories=[],
        )

        service = TransactionService(repository=transaction_repository_mock)
        service.account_service.find_by = AsyncMock(return_value=account)
        service.allocation_service.find_by = AsyncMock(return_value=allocation)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_list(finance=SimpleNamespace(id=uuid4()), payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "Transaction category list cannot be empty"

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_by_category_too_many_transactions(
        transaction_repository_mock: AsyncMock,
    ):
        """Test _persist_by_category with more than 12 transactions"""
        from app.domain.finance.transaction.schema import (
            PayloadTransactionCreateListCategoryItemSchema,
            PayloadTransactionCreateListItemSchema,
        )
        
        current_year = utcnow().year
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())
        category_id = uuid4()

        # Create 13 transactions (more than 12)
        transactions = [
            PayloadTransactionCreateListItemSchema(
                reference_month=i,
                amount=100.0,
                status=TransactionStatusEnum.PAID,
            )
            for i in range(1, 14)
        ]
        
        category_item = PayloadTransactionCreateListCategoryItemSchema(
            category_id=category_id,
            type=TransactionTypeEnum.EXPENSE,
            description="Test",
            transactions=transactions,
        )

        service = TransactionService(repository=transaction_repository_mock)
        service.category_service.find_by = AsyncMock(return_value=SimpleNamespace(id=category_id))

        with pytest.raises(HTTPException) as exc_info:
            await service._persist_by_category(
                finance=finance,
                payload=category_item,
                account=account,
                allocation=allocation,
                reference_year=current_year,
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert "Invalid number of transactions" in exc_info.value.detail

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_updates_existing_transaction(
        transaction_repository_mock: AsyncMock,
    ):
        """Test _persist when transaction already exists (with_throw=False)"""
        current_date = utcnow()
        current_year = current_date.year
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())
        category = SimpleNamespace(id=uuid4())

        payload = PayloadTransactionCreateSchema(
            type=TransactionTypeEnum.EXPENSE,
            amount=200.0,
            status=TransactionStatusEnum.PAID,
            account_id=account.id,
            allocation_id=allocation.id,
            category_id=category.id,
            description="Updated Description",
            transaction_date=date(current_year, 1, 15),
            paid_at=current_date,
        )

        existing_transaction = SimpleNamespace(
            id=uuid4(),
            type=TransactionTypeEnum.EXPENSE,
            amount=100.0,
            status=TransactionStatusEnum.PAID,
            account_id=account.id,
            allocation_id=allocation.id,
            category_id=category.id,
            description="Old Description",
            transaction_date=date(current_year, 1, 15),
            paid_at=current_date,
        )

        service = TransactionService(repository=transaction_repository_mock)
        service.find_by = AsyncMock(return_value=existing_transaction)
        transaction_repository_mock.update.return_value = existing_transaction

        result = await service._persist(
            finance=finance,
            account=account,
            category=category,
            allocation=allocation,
            payload=payload,
            with_throw=False,
        )

        # Verify that update was called (not save)
        transaction_repository_mock.update.assert_awaited_once()
        transaction_repository_mock.save.assert_not_awaited()
        assert result == existing_transaction

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_creates_separate_transactions_for_different_dates(
        transaction_repository_mock: AsyncMock,
    ):
        """Verify that transactions with different transaction_dates are created separately"""
        current_date = utcnow()
        current_year = current_date.year
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())
        category = SimpleNamespace(id=uuid4())

        # First transaction for January
        payload_jan = PayloadTransactionCreateSchema(
            type=TransactionTypeEnum.EXPENSE,
            amount=100.0,
            status=TransactionStatusEnum.PAID,
            account_id=account.id,
            allocation_id=allocation.id,
            category_id=category.id,
            description="January Transaction",
            transaction_date=date(current_year, 1, 15),
            paid_at=current_date,
        )
        
        # Second transaction for February with different date
        payload_feb = PayloadTransactionCreateSchema(
            type=TransactionTypeEnum.EXPENSE,
            amount=200.0,
            status=TransactionStatusEnum.PAID,
            account_id=account.id,
            allocation_id=allocation.id,
            category_id=category.id,
            description="February Transaction",
            transaction_date=date(current_year, 2, 15),
            paid_at=current_date,
        )

        service = TransactionService(repository=transaction_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        
        # Mock save to return transaction as-is
        def save_side_effect(entity):
            return entity
        
        transaction_repository_mock.save.side_effect = save_side_effect

        # Create both transactions
        result_jan = await service._persist(
            finance=finance,
            account=account,
            category=category,
            allocation=allocation,
            payload=payload_jan,
            with_throw=False,
        )
        
        result_feb = await service._persist(
            finance=finance,
            account=account,
            category=category,
            allocation=allocation,
            payload=payload_feb,
            with_throw=False,
        )

        # Verify that find_by was called with transaction_date for both
        assert service.find_by.await_count == 2
        
        # Check that the calls included transaction_date
        first_call_kwargs = service.find_by.call_args_list[0][1]
        assert first_call_kwargs["transaction_date"] == date(current_year, 1, 15)
        
        second_call_kwargs = service.find_by.call_args_list[1][1]
        assert second_call_kwargs["transaction_date"] == date(current_year, 2, 15)
        
        # Verify both transactions have different dates
        assert result_jan.transaction_date == date(current_year, 1, 15)
        assert result_feb.transaction_date == date(current_year, 2, 15)
        assert result_jan.transaction_date != result_feb.transaction_date
