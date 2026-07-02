import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from http import HTTPStatus

from fastapi import HTTPException

from app.domain.finance.expense.repository import ExpenseRepository
from app.domain.finance.expense.service import ExpenseService
from app.domain.finance.expense.schema import PayloadExpenseCreateSchema
from app.domain.finance.expense_month.schema import PayloadExpenseMonthPersistSchema
from app.domain.finance.account.service import AccountService
from app.domain.finance.category.service import CategoryService
from app.domain.finance.allocation.service import AllocationService
from app.domain.finance.expense_month.service import ExpenseMonthService
from app.domain.finance.schema import FinanceCreateCategorySchema
from app.models import (
    Expense,
    Finance,
    Account,
    Category,
    Allocation,
    CategoryTypeEnum,
)


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
def account():
    account = MagicMock(spec=Account)
    account.id = uuid4()
    account.finance_id = uuid4()
    return account


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


@pytest.fixture
def expense(account, category, allocation):
    expense = MagicMock(spec=Expense)
    expense.id = uuid4()
    expense.finance_id = account.finance_id
    expense.account_id = account.id
    expense.category_id = category.id
    expense.allocation_id = allocation.id
    return expense


class TestExpenseServiceCreate:
    @pytest.mark.asyncio
    async def test_create_expense_success(
        self, expense_service_with_mocks, finance, account, category, allocation, expense
    ):
        payload = PayloadExpenseCreateSchema(
            account_id=account.id,
            category_id=category.id,
            allocation_id=allocation.id,
            description="Test Expense",
            reference_day=1,
            reference_year=2026,
            months=[],
        )

        expense_service_with_mocks.account_service.find_by = AsyncMock(
            return_value=account
        )
        expense_service_with_mocks.category_service.find_by = AsyncMock(
            return_value=category
        )
        expense_service_with_mocks.allocation_service.find_by = AsyncMock(
            return_value=allocation
        )
        expense_service_with_mocks.persist = AsyncMock(return_value=expense)

        result = await expense_service_with_mocks.create(
            finance=finance, payload=payload
        )

        assert result.id == expense.id
        expense_service_with_mocks.persist.assert_called_once()


class TestExpenseServiceValidateRelations:
    @pytest.mark.asyncio
    async def test_validate_relations_success(
        self, expense_service_with_mocks, finance, account, allocation
    ):
        expense_service_with_mocks.account_service.find_by = AsyncMock(
            return_value=account
        )
        expense_service_with_mocks.allocation_service.find_by = AsyncMock(
            return_value=allocation
        )

        acc, alloc = await expense_service_with_mocks._validate_relations(
            finance=finance,
            account_id=account.id,
            allocation_id=allocation.id,
        )

        assert acc.id == account.id
        assert alloc.id == allocation.id

    @pytest.mark.asyncio
    async def test_validate_relations_account_not_found(
        self, expense_service_with_mocks, finance, allocation
    ):
        expense_service_with_mocks.account_service.find_by = AsyncMock(
            return_value=None
        )

        with pytest.raises(HTTPException) as exc_info:
            await expense_service_with_mocks._validate_relations(
                finance=finance,
                account_id=uuid4(),
                allocation_id=allocation.id,
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert "Account" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_validate_relations_allocation_not_found(
        self, expense_service_with_mocks, finance, account
    ):
        expense_service_with_mocks.account_service.find_by = AsyncMock(
            return_value=account
        )
        expense_service_with_mocks.allocation_service.find_by = AsyncMock(
            return_value=None
        )

        with pytest.raises(HTTPException) as exc_info:
            await expense_service_with_mocks._validate_relations(
                finance=finance,
                account_id=account.id,
                allocation_id=uuid4(),
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert "Allocation" in exc_info.value.detail


class TestExpenseServiceValidateCategory:
    @pytest.mark.asyncio
    async def test_validate_category_success(
        self, expense_service_with_mocks, category
    ):
        expense_service_with_mocks.category_service.find_by = AsyncMock(
            return_value=category
        )

        result = await expense_service_with_mocks._validate_category(
            category_id=category.id, finance_id=uuid4()
        )

        assert result.id == category.id

    @pytest.mark.asyncio
    async def test_validate_category_not_found(self, expense_service_with_mocks):
        expense_service_with_mocks.category_service.find_by = AsyncMock(
            return_value=None
        )

        with pytest.raises(HTTPException) as exc_info:
            await expense_service_with_mocks._validate_category(
                category_id=uuid4(), finance_id=uuid4()
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert "not found" in exc_info.value.detail


class TestExpenseServicePersist:
    @pytest.mark.asyncio
    async def test_persist_new_expense_success(
        self, expense_service_with_mocks, finance, account, category, allocation, expense
    ):
        payload = PayloadExpenseCreateSchema(
            account_id=account.id,
            category_id=category.id,
            allocation_id=allocation.id,
            description="Test Expense",
            reference_day=1,
            reference_year=2026,
            months=[],
        )

        with patch.object(
            expense_service_with_mocks, "find_by", new_callable=AsyncMock
        ) as mock_find:
            mock_find.side_effect = [None, expense]
            expense_service_with_mocks.repository.save = AsyncMock(return_value=expense)
            expense_service_with_mocks.expense_month_service.persist_list = AsyncMock(
                return_value=[]
            )

            result = await expense_service_with_mocks.persist(
                finance=finance,
                account=account,
                category=category,
                allocation=allocation,
                payload=payload,
            )

            assert result.id == expense.id

    @pytest.mark.asyncio
    async def test_persist_existing_expense_with_throw(
        self, expense_service_with_mocks, finance, account, category, allocation, expense
    ):
        payload = PayloadExpenseCreateSchema(
            account_id=account.id,
            category_id=category.id,
            allocation_id=allocation.id,
            description="Test Expense",
            reference_day=1,
            reference_year=2026,
            months=[],
        )

        with patch.object(
            expense_service_with_mocks, "find_by", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = expense

            with pytest.raises(HTTPException) as exc_info:
                await expense_service_with_mocks.persist(
                    finance=finance,
                    account=account,
                    category=category,
                    allocation=allocation,
                    payload=payload,
                    with_throw=True,
                )

            assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_persist_existing_expense_without_throw(
        self, expense_service_with_mocks, finance, account, category, allocation, expense
    ):
        payload = PayloadExpenseCreateSchema(
            account_id=account.id,
            category_id=category.id,
            allocation_id=allocation.id,
            description="Updated Expense",
            reference_day=1,
            reference_year=2026,
            months=[],
        )

        with patch.object(
            expense_service_with_mocks, "find_by", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = expense
            expense_service_with_mocks.repository.update = AsyncMock(
                return_value=expense
            )
            expense_service_with_mocks.expense_month_service.persist_list = AsyncMock(
                return_value=[]
            )

            result = await expense_service_with_mocks.persist(
                finance=finance,
                account=account,
                category=category,
                allocation=allocation,
                payload=payload,
                with_throw=False,
            )

            assert result.id == expense.id


class TestExpenseServiceCreateByAccount:
    @pytest.mark.asyncio
    async def test_create_by_account_success(
        self, expense_service_with_mocks, finance, account, allocation, category, expense
    ):
        payload_categories = [
            FinanceCreateCategorySchema(
                name="Food",
                type=CategoryTypeEnum.FOOD,
                description="Food expenses",
                months=[
                    PayloadExpenseMonthPersistSchema(
                        reference_month=1,
                        amount=Decimal("100.00"),
                    )
                ],
            )
        ]

        expense_service_with_mocks.category_service.persist = AsyncMock(
            return_value=category
        )
        expense_service_with_mocks.persist = AsyncMock(return_value=expense)

        result = await expense_service_with_mocks.create_by_account(
            finance=finance,
            account=account,
            allocation=allocation,
            reference_day=1,
            reference_year=2026,
            payload_categories=payload_categories,
        )

        assert len(result) == 1
        assert result[0].id == expense.id

    @pytest.mark.asyncio
    async def test_create_by_account_empty_categories(
        self, expense_service_with_mocks, finance, account, allocation
    ):
        result = await expense_service_with_mocks.create_by_account(
            finance=finance,
            account=account,
            allocation=allocation,
            reference_day=1,
            reference_year=2026,
            payload_categories=[],
        )

        assert len(result) == 0
