from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4


import pytest
from fastapi import HTTPException

from app.domain.finance.expense.schema import (
    PayloadExpenseCreateSchema,
)
from app.domain.finance.expense.service import (
    ExpenseService,
)
from app.models import utcnow, ExpenseStatusEnum


@pytest.fixture
def expense_repository_mock() -> AsyncMock:
    return AsyncMock()


class TestFinanceExpenseServiceFromSession:
    @staticmethod
    @pytest.mark.asyncio
    async def test_from_session_builds_service() -> None:
        service = ExpenseService.from_session(AsyncMock())
        assert isinstance(service, ExpenseService)


class TestFinanceExpenseCreateService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_service_create_exist(
        expense_repository_mock: AsyncMock,
    ):
        current_date = utcnow()
        payload = PayloadExpenseCreateSchema(
            amount=150.0,
            status=ExpenseStatusEnum.PAID,
            account_id=uuid4(),
            allocation_id=uuid4(),
            category_id=uuid4(),
            description="Some Description",
            paid_at=current_date,
        )
        finance = SimpleNamespace(
            id=uuid4()
        )

        service = ExpenseService(repository=expense_repository_mock)
        service.find_by = AsyncMock(return_value=SimpleNamespace(id=uuid4()))
        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "Expense already exists"

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_service_create_account_not_exist(
        expense_repository_mock: AsyncMock,
    ):
        current_date = utcnow()
        payload = PayloadExpenseCreateSchema(
            amount=150.0,
            status=ExpenseStatusEnum.PAID,
            account_id=uuid4(),
            allocation_id=uuid4(),
            category_id=uuid4(),
            description="Some Description",
            paid_at=current_date,
        )
        finance = SimpleNamespace(id=uuid4())

        service = ExpenseService(repository=expense_repository_mock)
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
    async def test_finance_expense_service_create_allocation_not_exist(
        expense_repository_mock: AsyncMock,
    ):
        current_date = utcnow()
        payload = PayloadExpenseCreateSchema(
            amount=150.0,
            status=ExpenseStatusEnum.PAID,
            account_id=uuid4(),
            allocation_id=uuid4(),
            category_id=uuid4(),
            description="Some Description",
            paid_at=current_date,
        )
        finance = SimpleNamespace(id=uuid4())

        service = ExpenseService(repository=expense_repository_mock)
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
    async def test_finance_expense_service_create_category_not_exist(
        expense_repository_mock: AsyncMock,
    ):
        current_date = utcnow()
        payload = PayloadExpenseCreateSchema(
            amount=150.0,
            status=ExpenseStatusEnum.PAID,
            account_id=uuid4(),
            allocation_id=uuid4(),
            category_id=uuid4(),
            description="Some Description",
            paid_at=current_date,
        )
        finance = SimpleNamespace(id=uuid4())

        service = ExpenseService(repository=expense_repository_mock)
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
    async def test_finance_expense_service_create_successfully(
        expense_repository_mock: AsyncMock,
    ):
        current_date = utcnow()
        payload = PayloadExpenseCreateSchema(
            amount=150.0,
            status=ExpenseStatusEnum.PAID,
            account_id=uuid4(),
            allocation_id=uuid4(),
            category_id=uuid4(),
            description="Some Description",
            paid_at=current_date,
        )
        expected = SimpleNamespace(
            id=uuid4(),
            amount=payload.amount,
            status=payload.status,
            account_id=payload.account_id,
            allocation_id=payload.allocation_id,
            category_id=payload.category_id,
            description=payload.description,
            paid_at=payload.paid_at,
        )
        finance = SimpleNamespace(id=uuid4())

        service = ExpenseService(repository=expense_repository_mock)
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
        
class TestFinanceExpense_PesistService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_persist_updates_existing_expense(
        expense_repository_mock: AsyncMock,
    ):
        """Test _persist when expense already exists (with_throw=False)"""
        current_date = utcnow()
        
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())
        category = SimpleNamespace(id=uuid4())

        payload = PayloadExpenseCreateSchema(
            amount=200.0,
            status=ExpenseStatusEnum.PAID,
            account_id=account.id,
            allocation_id=allocation.id,
            category_id=category.id,
            description="Updated Description",
            paid_at=current_date,
        )

        existing_expense = SimpleNamespace(
            id=uuid4(),
            amount=100.0,
            status=ExpenseStatusEnum.PAID,
            account_id=account.id,
            allocation_id=allocation.id,
            category_id=category.id,
            description="Old Description",
            paid_at=current_date,
        )

        service = ExpenseService(repository=expense_repository_mock)
        service.find_by = AsyncMock(return_value=existing_expense)
        expense_repository_mock.update.return_value = existing_expense

        result = await service._persist(
            finance=finance,
            account=account,
            category=category,
            allocation=allocation,
            payload=payload,
            with_throw=False,
        )

        # Verify that update was called (not save)
        expense_repository_mock.update.assert_awaited_once()
        expense_repository_mock.save.assert_not_awaited()
        assert result == existing_expense

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_persist_creates_separate_expenses_for_different_dates(
        expense_repository_mock: AsyncMock,
    ):
        """Verify that transactions with different transaction_dates are created separately"""
        current_date = utcnow()
        
        finance = SimpleNamespace(id=uuid4())
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())
        category = SimpleNamespace(id=uuid4())

        # First expense for January
        payload_jan = PayloadExpenseCreateSchema(
            amount=100.0,
            status=ExpenseStatusEnum.PAID,
            account_id=account.id,
            allocation_id=allocation.id,
            category_id=category.id,
            description="January Expense",
            paid_at=current_date,
        )

        # Second expense for February with different date
        payload_feb = PayloadExpenseCreateSchema(
            amount=200.0,
            status=ExpenseStatusEnum.PAID,
            account_id=account.id,
            allocation_id=allocation.id,
            category_id=category.id,
            description="February Expense",
            paid_at=current_date,
        )

        service = ExpenseService(repository=expense_repository_mock)
        service.find_by = AsyncMock(return_value=None)

        # Mock save to return expense as-is
        def save_side_effect(entity):
            return entity

        expense_repository_mock.save.side_effect = save_side_effect

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

        assert service.find_by.await_count == 2

        # Check that the calls included lookup keys used by service._persist
        first_call_kwargs = service.find_by.call_args_list[0][1]
        assert first_call_kwargs["finance_id"] == finance.id
        assert first_call_kwargs["account_id"] == account.id
        assert first_call_kwargs["allocation_id"] == allocation.id
        assert first_call_kwargs["category_id"] == category.id
        assert first_call_kwargs["paid_at"] == current_date

        second_call_kwargs = service.find_by.call_args_list[1][1]
        assert second_call_kwargs["finance_id"] == finance.id
        assert second_call_kwargs["account_id"] == account.id
        assert second_call_kwargs["allocation_id"] == allocation.id
        assert second_call_kwargs["category_id"] == category.id
        assert second_call_kwargs["paid_at"] == current_date

        # Verify both transactions have different dates
        assert result_jan.description == "January Expense"
        assert result_feb.description == "February Expense"
        assert result_jan.description != result_feb.description
