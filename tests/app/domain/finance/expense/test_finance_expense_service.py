from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.domain.finance.account.service import AccountService
from app.domain.finance.allocation.service import AllocationService
from app.domain.finance.category.service import CategoryService
from app.domain.finance.expense.repository import ExpenseRepository
from app.domain.finance.expense.schema import PayloadExpenseCreateSchema
from app.domain.finance.expense.service import ExpenseService
from app.domain.finance.expense_month.service import ExpenseMonthService
from app.domain.finance.months.schema import PayloadMonthPersistSchema

from app.models import (
    Allocation,
    Category,
    Finance,
    utcnow,
)


@pytest.fixture
def expense_repository_mock():
    return AsyncMock()


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def expense_service_with_mocks(mock_session):
    repository = AsyncMock(spec=ExpenseRepository)
    repository.session = mock_session
    account_service = AsyncMock(spec=AccountService)
    category_service = AsyncMock(spec=CategoryService)
    allocation_service = AsyncMock(spec=AllocationService)
    expense_month_service = AsyncMock(spec=ExpenseMonthService)

    return ExpenseService(
        repository=repository,
        account_service=account_service,
        category_service=category_service,
        allocation_service=allocation_service,
        expense_month_service=expense_month_service,
    )


@pytest.fixture
def finance():
    finance = MagicMock(spec=Finance)
    finance.id = uuid4()
    return finance


@pytest.fixture
def category():
    category = MagicMock(spec=Category)
    category.id = uuid4()
    category.finance_id = uuid4()
    return category


@pytest.fixture
def allocation():
    allocation = MagicMock(spec=Allocation)
    allocation.id = uuid4()
    return allocation


class TestFinanceExpenseServiceCreate:
    @staticmethod
    @pytest.mark.asyncio
    async def test_expense_create_with_invalid_allocation(
        expense_repository_mock,
        finance,
        category,
        allocation,
    ):
        current_year = utcnow().year
        payload = PayloadExpenseCreateSchema(
            payee="Test Payee",
            months=[],
            category_id=category.id,
            allocation_id=allocation.id,
            description="Test Expense",
            reference_day=10,
            reference_year=current_year,
        )

        service = ExpenseService(repository=expense_repository_mock)
        service.allocation_service.find_by = AsyncMock(return_value=None)
        service.category_service.find_by = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Allocation with this id {allocation.id} does not exist"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_expense_create_with_invalid_category(
        expense_repository_mock,
        finance,
        category,
        allocation,
    ):
        current_year = utcnow().year
        payload = PayloadExpenseCreateSchema(
            payee="Test Payee",
            months=[],
            category_id=category.id,
            allocation_id=allocation.id,
            description="Test Expense",
            reference_day=10,
            reference_year=current_year,
        )

        service = ExpenseService(repository=expense_repository_mock)
        service.allocation_service.find_by = AsyncMock(return_value=allocation)
        service.category_service.find_by = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Category {category.id} not found for finance {finance.id}"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_expense_create_successfully(
        expense_repository_mock,
        finance,
        category,
        allocation,
    ):
        current_year = utcnow().year
        payload = PayloadExpenseCreateSchema(
            payee="Test Payee",
            months=[],
            category_id=category.id,
            allocation_id=allocation.id,
            description="Test Expense",
            reference_day=10,
            reference_year=current_year,
        )

        saved_expense = SimpleNamespace(
            id=uuid4(),
            payee=payload.payee,
            category_id=category.id,
            description=payload.description,
            allocation_id=allocation.id,
        )

        expense_repository_mock.save.return_value = saved_expense

        service = ExpenseService(repository=expense_repository_mock)
        service.allocation_service.find_by = AsyncMock(return_value=allocation)
        service.category_service.find_by = AsyncMock(return_value=category)
        service.find_by = AsyncMock(side_effect=[None, saved_expense])
        service.expense_month_service.persist_list = AsyncMock(return_value=[])

        result = await service.create(finance=finance, payload=payload)
        assert result == saved_expense
        expense_repository_mock.save.assert_awaited_once()


class TestFinanceExpensePersistService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_persist_service_invalid_year(
        expense_repository_mock, finance, category, allocation
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
        payee = "Test Payee"
        description = "Some Description"
        current_year = utcnow().year
        reference_day = 10
        reference_year = current_year + 1

        service = ExpenseService(repository=expense_repository_mock)
        with pytest.raises(HTTPException) as exc_info:
            await service.persist(
                payee=payee,
                months=months,
                category=category,
                allocation=allocation,
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
    async def test_finance_expense_persist_service_exist_expense_with_throw(
        expense_repository_mock, finance, category, allocation
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
        payee = "Test Payee"
        description = "Some Description"
        current_year = utcnow().year
        reference_day = 10
        reference_year = current_year

        exist_expense = SimpleNamespace(
            id=uuid4(),
            payee=payee,
            category_id=category.id,
            description=description,
            allocation_id=allocation.id,
        )
        expense_repository_mock.find_by.return_value = exist_expense
        service = ExpenseService(repository=expense_repository_mock)
        with pytest.raises(HTTPException) as exc_info:
            await service.persist(
                payee=payee,
                months=months,
                category=category,
                allocation=allocation,
                with_throw=True,
                description=description,
                reference_day=reference_day,
                reference_year=reference_year,
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == f"Expense with payee {payee} already exists"

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_persist_service_exist_expense_without_throw(
        expense_repository_mock, finance, category, allocation
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
        payee = "Test Payee"
        description = "Some Description"
        current_year = utcnow().year
        reference_day = 10
        reference_year = current_year

        exist_expense = SimpleNamespace(
            id=uuid4(),
            payee=payee,
            category_id=category.id,
            description=description,
            allocation_id=allocation.id,
        )
        expense_repository_mock.find_by.return_value = exist_expense
        expense_repository_mock.update.return_value = exist_expense
        service = ExpenseService(repository=expense_repository_mock)
        service.expense_month_service.persist_list = AsyncMock(return_value=months)
        result = await service.persist(
            payee=payee,
            months=months,
            category=category,
            allocation=allocation,
            with_throw=False,
            description=description,
            reference_day=reference_day,
            reference_year=reference_year,
        )
        assert result == exist_expense
        expense_repository_mock.find_by.assert_awaited_once()
        expense_repository_mock.update.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_persist_service_save_when_not_exist_expense(
        expense_repository_mock, finance, category, allocation
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
        payee = "Test Payee"
        description = "Some Description"
        current_year = utcnow().year
        reference_day = 10
        reference_year = current_year

        created_expense = SimpleNamespace(
            id=uuid4(),
            payee=payee,
            category_id=category.id,
            description=description,
            allocation_id=allocation.id,
        )

        expense_repository_mock.save.return_value = created_expense
        service = ExpenseService(repository=expense_repository_mock)
        service.find_by = AsyncMock(side_effect=[None, created_expense])
        service.expense_month_service.persist_list = AsyncMock(return_value=months)
        result = await service.persist(
            payee=payee,
            months=months,
            category=category,
            allocation=allocation,
            with_throw=False,
            description=description,
            reference_day=reference_day,
            reference_year=reference_year,
        )
        assert result == created_expense
        expense_repository_mock.save.assert_awaited_once()
