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
from app.domain.finance.schema import (
    PayloadFinanceCategoryPersistSchema,
    PayloadFinanceChildrenExpensePersistSchema,
    PayloadFinanceExpensePersistSchema,
)
from app.models import (
    Account,
    Allocation,
    Category,
    CategoryTypeEnum,
    Expense,
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
def expense_persist_children():
    children: list[PayloadFinanceChildrenExpensePersistSchema] = [
        PayloadFinanceChildrenExpensePersistSchema(
            name="Children Name 1",
            type=CategoryTypeEnum.ENTERTAINMENT,
            amount=44.90,
            description="Children Description 1",
        ),
        PayloadFinanceChildrenExpensePersistSchema(
            name="Children Name 2",
            type=CategoryTypeEnum.ENTERTAINMENT,
            amount=22.45,
            description="Children Description 2",
        ),
        PayloadFinanceChildrenExpensePersistSchema(
            name="Children Name 3",
            type=CategoryTypeEnum.ENTERTAINMENT,
            amount=19.90,
            description="Children Description 3",
        ),
        PayloadFinanceChildrenExpensePersistSchema(
            name="Children Name 4",
            type=CategoryTypeEnum.ENTERTAINMENT,
            amount=9.90,
            description="Children Description 4",
        ),
        PayloadFinanceChildrenExpensePersistSchema(
            name="Children Name 5",
            type=CategoryTypeEnum.ENTERTAINMENT,
            amount=50,
            description="Children Description 5",
        ),
    ]
    return children


@pytest.fixture()
def expense_persist(expense_persist_children):
    expenses: list[PayloadFinanceExpensePersistSchema] = [
        PayloadFinanceExpensePersistSchema(amount=100.00, children=None),
        PayloadFinanceExpensePersistSchema(
            amount=200.00, children=None, reference_month=2
        ),
        PayloadFinanceExpensePersistSchema(
            amount=300.00, children=expense_persist_children, reference_month=3
        ),
    ]
    return expenses


@pytest.fixture()
def payload_finance_category_persist(expense_persist):
    return PayloadFinanceCategoryPersistSchema(
        name="Category Name",
        type=CategoryTypeEnum.ENTERTAINMENT,
        description="Category Description",
        expenses=expense_persist,
    )


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


class TestFinanceExpensePersistService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_persist_service_invalid_year(
        expense_repository_mock, account, finance, category, allocation
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

        description = "Some Description"
        current_year = utcnow().year
        reference_day = 10
        reference_year = current_year + 1

        service = ExpenseService(repository=expense_repository_mock)
        with pytest.raises(HTTPException) as exc_info:
            await service.persist(
                months=months,
                account=account,
                finance=finance,
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
        expense_repository_mock, account, finance, category, allocation
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

        description = "Some Description"
        current_year = utcnow().year
        reference_day = 10
        reference_year = current_year

        exist_expense = SimpleNamespace(
            id=uuid4(),
            account_id=account.id,
            category_id=category.id,
            description=description,
            allocation_id=allocation.id,
        )
        expense_repository_mock.find_by.return_value = exist_expense
        service = ExpenseService(repository=expense_repository_mock)
        with pytest.raises(HTTPException) as exc_info:
            await service.persist(
                months=months,
                account=account,
                finance=finance,
                category=category,
                allocation=allocation,
                with_throw=True,
                description=description,
                reference_day=reference_day,
                reference_year=reference_year,
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "Expense already exists"

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_persist_service_exist_expense_without_throw(
        expense_repository_mock, account, finance, category, allocation
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

        description = "Some Description"
        current_year = utcnow().year
        reference_day = 10
        reference_year = current_year

        exist_expense = SimpleNamespace(
            id=uuid4(),
            account_id=account.id,
            category_id=category.id,
            description=description,
            allocation_id=allocation.id,
        )
        expense_repository_mock.find_by.return_value = exist_expense
        expense_repository_mock.update.return_value = exist_expense
        service = ExpenseService(repository=expense_repository_mock)
        service.expense_month_service.persist_list = AsyncMock(return_value=months)
        result = await service.persist(
            months=months,
            account=account,
            finance=finance,
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
        expense_repository_mock, account, finance, category, allocation
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

        description = "Some Description"
        current_year = utcnow().year
        reference_day = 10
        reference_year = current_year

        created_expense = SimpleNamespace(
            id=uuid4(),
            account_id=account.id,
            category_id=category.id,
            description=description,
            allocation_id=allocation.id,
        )

        expense_repository_mock.save.return_value = created_expense
        service = ExpenseService(repository=expense_repository_mock)
        service.find_by = AsyncMock(side_effect=[None, created_expense])
        service.expense_month_service.persist_list = AsyncMock(return_value=months)
        result = await service.persist(
            months=months,
            account=account,
            finance=finance,
            category=category,
            allocation=allocation,
            with_throw=False,
            description=description,
            reference_day=reference_day,
            reference_year=reference_year,
        )
        assert result == created_expense
        expense_repository_mock.save.assert_awaited_once()


class TestExpenseServiceCreate:
    @staticmethod
    @pytest.mark.asyncio
    async def test_expense_create_with_invalid_account(
        expense_repository_mock,
        finance,
        account,
        category,
        allocation,
    ):
        current_year = utcnow().year
        payload = PayloadExpenseCreateSchema(
            months=[],
            account_id=account.id,
            category_id=category.id,
            allocation_id=allocation.id,
            description="Test Expense",
            reference_day=10,
            reference_year=current_year,
        )

        service = ExpenseService(repository=expense_repository_mock)
        service.account_service.find_by = AsyncMock(return_value=None)
        service.allocation_service.find_by = AsyncMock(return_value=None)
        service.category_service.find_by = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail == f"Account with this id {account.id} does not exist"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_expense_create_with_invalid_allocation(
        expense_repository_mock,
        finance,
        account,
        category,
        allocation,
    ):
        current_year = utcnow().year
        payload = PayloadExpenseCreateSchema(
            months=[],
            account_id=account.id,
            category_id=category.id,
            allocation_id=allocation.id,
            description="Test Expense",
            reference_day=10,
            reference_year=current_year,
        )

        service = ExpenseService(repository=expense_repository_mock)
        service.account_service.find_by = AsyncMock(return_value=account)
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
        account,
        category,
        allocation,
    ):
        current_year = utcnow().year
        payload = PayloadExpenseCreateSchema(
            months=[],
            account_id=account.id,
            category_id=category.id,
            allocation_id=allocation.id,
            description="Test Expense",
            reference_day=10,
            reference_year=current_year,
        )

        service = ExpenseService(repository=expense_repository_mock)
        service.account_service.find_by = AsyncMock(return_value=account)
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
        account,
        category,
        allocation,
    ):
        current_year = utcnow().year
        payload = PayloadExpenseCreateSchema(
            months=[],
            account_id=account.id,
            category_id=category.id,
            allocation_id=allocation.id,
            description="Test Expense",
            reference_day=10,
            reference_year=current_year,
        )

        saved_expense = SimpleNamespace(
            id=uuid4(),
            account_id=account.id,
            category_id=category.id,
            description=payload.description,
            allocation_id=allocation.id,
        )

        expense_repository_mock.save.return_value = saved_expense

        service = ExpenseService(repository=expense_repository_mock)
        service.account_service.find_by = AsyncMock(return_value=account)
        service.allocation_service.find_by = AsyncMock(return_value=allocation)
        service.category_service.find_by = AsyncMock(return_value=category)
        service.find_by = AsyncMock(side_effect=[None, saved_expense])
        service.expense_month_service.persist_list = AsyncMock(return_value=[])

        result = await service.create(finance=finance, payload=payload)
        assert result == saved_expense
        expense_repository_mock.save.assert_awaited_once()


class TestExpenseServicePersistByCategory:
    @staticmethod
    @pytest.mark.asyncio
    async def test_expense_persist_by_category_return_empty_when_no_expenses(
        expense_repository_mock,
        account,
        finance,
        category,
        allocation,
        payload_finance_category_persist,
    ):
        current_datetime = utcnow()
        payload = payload_finance_category_persist
        payload.expenses = []

        service = ExpenseService(repository=expense_repository_mock)

        service.category_service = AsyncMock(spec=CategoryService)
        service.category_service.persist = AsyncMock(return_value=category)

        result = await service.persist_by_category(
            finance=finance,
            account=account,
            payload=payload,
            allocation=allocation,
            reference_day=10,
            reference_year=current_datetime.year,
        )

        assert len(result) == 0
        service.category_service.persist.assert_called_once_with(
            finance=finance,
            payload=payload,
            with_throw=False,
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_expense_persist_by_category_with_expenses_without_children(
        expense_repository_mock,
        account,
        finance,
        category,
        allocation,
        expense_persist,
    ):
        """Test persist_by_category with expenses but no children (non-CREDIT_CARD type)"""
        current_datetime = utcnow()

        payload = PayloadFinanceCategoryPersistSchema(
            name="Category Name",
            type=CategoryTypeEnum.ENTERTAINMENT,
            description="Category Description",
            expenses=expense_persist,
        )

        expense_mock = MagicMock(spec=SimpleNamespace)
        expense_mock.id = uuid4()

        service = ExpenseService(repository=expense_repository_mock)
        service.category_service = AsyncMock(spec=CategoryService)
        service.category_service.persist = AsyncMock(return_value=category)
        service.persist = AsyncMock(return_value=expense_mock)
        service.persist_children = AsyncMock(return_value=[])

        result = await service.persist_by_category(
            finance=finance,
            account=account,
            payload=payload,
            allocation=allocation,
            reference_day=10,
            reference_year=current_datetime.year,
        )

        assert len(result) == 1
        assert result[0].id == expense_mock.id
        service.category_service.persist.assert_called_once_with(
            finance=finance,
            payload=payload,
            with_throw=False,
        )
        service.persist.assert_called_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_expense_persist_by_category_with_credit_card_expenses_and_children(
        expense_repository_mock,
        account,
        finance,
        allocation,
        expense_persist_children,
    ):
        """Test persist_by_category with CREDIT_CARD type and children"""
        current_datetime = utcnow()

        credit_card_expenses = [
            PayloadFinanceExpensePersistSchema(
                amount=300.00, children=expense_persist_children, reference_month=3
            )
        ]

        payload = PayloadFinanceCategoryPersistSchema(
            name="Credit Card",
            type=CategoryTypeEnum.CREDIT_CARD,
            description="Credit Card Description",
            expenses=credit_card_expenses,
        )

        category = MagicMock(spec=Category)
        category.id = uuid4()
        category.finance_id = uuid4()
        category.description = "Credit Card Description"

        parent_expense = MagicMock(spec=SimpleNamespace)
        parent_expense.id = uuid4()

        children_expense_1 = MagicMock(spec=SimpleNamespace)
        children_expense_1.id = uuid4()

        children_expense_2 = MagicMock(spec=SimpleNamespace)
        children_expense_2.id = uuid4()

        service = ExpenseService(repository=expense_repository_mock)
        service.category_service = AsyncMock(spec=CategoryService)
        service.category_service.persist = AsyncMock(return_value=category)
        service.persist = AsyncMock(return_value=parent_expense)
        service.persist_children = AsyncMock(
            return_value=[children_expense_1, children_expense_2]
        )

        result = await service.persist_by_category(
            finance=finance,
            account=account,
            payload=payload,
            allocation=allocation,
            reference_day=10,
            reference_year=current_datetime.year,
        )

        assert len(result) == 3
        assert result[0].id == parent_expense.id
        assert result[1].id == children_expense_1.id
        assert result[2].id == children_expense_2.id
        service.persist_children.assert_called_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_expense_persist_by_category_category_service_called_with_throw_false(
        expense_repository_mock,
        account,
        finance,
        category,
        allocation,
        payload_finance_category_persist,
    ):
        """Test that category_service.persist is called with with_throw=False"""
        current_datetime = utcnow()
        payload = payload_finance_category_persist

        service = ExpenseService(repository=expense_repository_mock)
        service.category_service = AsyncMock(spec=CategoryService)
        service.category_service.persist = AsyncMock(return_value=category)
        service.persist = AsyncMock(return_value=MagicMock())

        await service.persist_by_category(
            finance=finance,
            account=account,
            payload=payload,
            allocation=allocation,
            reference_day=10,
            reference_year=current_datetime.year,
        )

        service.category_service.persist.assert_called_once()
        call_kwargs = service.category_service.persist.call_args[1]
        assert call_kwargs["with_throw"] is False

    @staticmethod
    @pytest.mark.asyncio
    async def test_expense_persist_by_category_persist_called_with_correct_params(
        expense_repository_mock,
        account,
        finance,
        category,
        allocation,
        expense_persist,
    ):
        """Test that persist method is called with correct parameters"""
        current_datetime = utcnow()

        payload = PayloadFinanceCategoryPersistSchema(
            name="Test Category",
            type=CategoryTypeEnum.FOOD,
            description="Test Description",
            expenses=expense_persist,
        )

        expense_mock = MagicMock()

        service = ExpenseService(repository=expense_repository_mock)
        service.category_service = AsyncMock(spec=CategoryService)
        service.category_service.persist = AsyncMock(return_value=category)
        service.persist = AsyncMock(return_value=expense_mock)

        await service.persist_by_category(
            finance=finance,
            account=account,
            payload=payload,
            allocation=allocation,
            reference_day=15,
            reference_year=current_datetime.year,
        )

        service.persist.assert_called_once()
        call_kwargs = service.persist.call_args[1]
        assert call_kwargs["account"] == account
        assert call_kwargs["finance"] == finance
        assert call_kwargs["category"] == category
        assert call_kwargs["allocation"] == allocation
        assert call_kwargs["description"] == category.description
        assert call_kwargs["reference_day"] == 15
        assert call_kwargs["reference_year"] == current_datetime.year
        assert call_kwargs["with_throw"] is False

    @staticmethod
    @pytest.mark.asyncio
    async def test_expense_persist_by_category_credit_card_persist_children_called(
        expense_repository_mock,
        account,
        finance,
        allocation,
        expense_persist_children,
    ):
        """Test that persist_children is called for CREDIT_CARD type with children"""
        current_datetime = utcnow()

        credit_card_expenses = [
            PayloadFinanceExpensePersistSchema(
                amount=300.00, children=expense_persist_children, reference_month=3
            )
        ]

        payload = PayloadFinanceCategoryPersistSchema(
            name="Credit Card",
            type=CategoryTypeEnum.CREDIT_CARD,
            description="Credit Card",
            expenses=credit_card_expenses,
        )

        category = MagicMock(spec=Category)
        category.id = uuid4()
        category.description = "Credit Card"

        parent_expense = MagicMock()
        parent_expense.id = uuid4()

        service = ExpenseService(repository=expense_repository_mock)
        service.category_service = AsyncMock(spec=CategoryService)
        service.category_service.persist = AsyncMock(return_value=category)
        service.persist = AsyncMock(return_value=parent_expense)
        service.persist_children = AsyncMock(return_value=[])

        await service.persist_by_category(
            finance=finance,
            account=account,
            payload=payload,
            allocation=allocation,
            reference_day=10,
            reference_year=current_datetime.year,
        )

        service.persist_children.assert_called_once()
        call_kwargs = service.persist_children.call_args[1]
        assert call_kwargs["parent"] == parent_expense
        assert call_kwargs["reference_day"] == 10
        assert call_kwargs["reference_year"] == current_datetime.year
        assert call_kwargs["reference_month"] == 3

    @staticmethod
    @pytest.mark.asyncio
    async def test_expense_persist_by_category_returns_parent_and_children_expenses(
        expense_repository_mock,
        account,
        finance,
        allocation,
        expense_persist_children,
    ):
        """Test that the method returns both parent and children expenses in correct order"""
        current_datetime = utcnow()

        credit_card_expenses = [
            PayloadFinanceExpensePersistSchema(
                amount=300.00, children=expense_persist_children, reference_month=3
            )
        ]

        payload = PayloadFinanceCategoryPersistSchema(
            name="Credit Card",
            type=CategoryTypeEnum.CREDIT_CARD,
            description="Credit Card",
            expenses=credit_card_expenses,
        )

        category = MagicMock(spec=Category)
        category.id = uuid4()
        category.description = "Credit Card"

        parent_expense = MagicMock()
        parent_expense.id = uuid4()

        child_1 = MagicMock()
        child_1.id = uuid4()

        child_2 = MagicMock()
        child_2.id = uuid4()

        service = ExpenseService(repository=expense_repository_mock)
        service.category_service = AsyncMock(spec=CategoryService)
        service.category_service.persist = AsyncMock(return_value=category)
        service.persist = AsyncMock(return_value=parent_expense)
        service.persist_children = AsyncMock(return_value=[child_1, child_2])

        result = await service.persist_by_category(
            finance=finance,
            account=account,
            payload=payload,
            allocation=allocation,
            reference_day=10,
            reference_year=current_datetime.year,
        )

        assert len(result) == 3
        assert result[0] == parent_expense
        assert result[1] == child_1
        assert result[2] == child_2


class TestExpenseServicePersistChildren:
    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_children_return_empty_when_no_children(
        expense_repository_mock,
    ):
        """Test persist_children returns empty list when children list is empty"""
        parent = MagicMock(spec=Expense)
        parent.finance = MagicMock(spec=Finance)
        parent.account = MagicMock(spec=Account)
        parent.allocation = MagicMock(spec=Allocation)

        service = ExpenseService(repository=expense_repository_mock)
        service.category_service = AsyncMock(spec=CategoryService)

        result = await service.persist_children(
            parent=parent,
            children=[],
            reference_day=10,
            reference_year=2024,
            reference_month=3,
        )

        assert len(result) == 0
        service.category_service.persist.assert_not_called()

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_children_with_single_child(
        expense_repository_mock,
    ):
        """Test persist_children with a single child"""
        parent = MagicMock(spec=Expense)
        parent.finance = MagicMock(spec=Finance)
        parent.account = MagicMock(spec=Account)
        parent.allocation = MagicMock(spec=Allocation)

        child_payload = PayloadFinanceChildrenExpensePersistSchema(
            name="Child 1",
            type=CategoryTypeEnum.ENTERTAINMENT,
            amount=50.00,
            description="Child Description 1",
        )

        category = MagicMock(spec=Category)
        category.id = uuid4()
        category.description = "Child 1"

        expense_child = MagicMock(spec=Expense)
        expense_child.id = uuid4()

        service = ExpenseService(repository=expense_repository_mock)
        service.category_service = AsyncMock(spec=CategoryService)
        service.category_service.persist = AsyncMock(return_value=category)
        service.persist = AsyncMock(return_value=expense_child)

        result = await service.persist_children(
            parent=parent,
            children=[child_payload],
            reference_day=10,
            reference_year=2024,
            reference_month=3,
        )

        assert len(result) == 1
        assert result[0].id == expense_child.id
        service.category_service.persist.assert_called_once()
        service.persist.assert_called_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_children_with_multiple_children(
        expense_repository_mock,
        expense_persist_children,
    ):
        """Test persist_children with multiple children"""
        parent = MagicMock(spec=Expense)
        parent.finance = MagicMock(spec=Finance)
        parent.account = MagicMock(spec=Account)
        parent.allocation = MagicMock(spec=Allocation)

        categories = [MagicMock(spec=Category) for _ in range(5)]
        expenses = [MagicMock(spec=Expense) for _ in range(5)]

        for cat, exp in zip(categories, expenses):
            cat.id = uuid4()
            cat.description = f"Category {cat.id}"
            exp.id = uuid4()

        service = ExpenseService(repository=expense_repository_mock)
        service.category_service = AsyncMock(spec=CategoryService)
        service.category_service.persist = AsyncMock(side_effect=categories)
        service.persist = AsyncMock(side_effect=expenses)

        result = await service.persist_children(
            parent=parent,
            children=expense_persist_children,
            reference_day=10,
            reference_year=2024,
            reference_month=3,
        )

        assert len(result) == 5
        assert service.category_service.persist.call_count == 5
        assert service.persist.call_count == 5

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_children_creates_category_with_throw_false(
        expense_repository_mock,
    ):
        """Test that category_service.persist is called with with_throw=False"""
        parent = MagicMock(spec=Expense)
        parent.finance = MagicMock(spec=Finance)
        parent.account = MagicMock(spec=Account)
        parent.allocation = MagicMock(spec=Allocation)

        child_payload = PayloadFinanceChildrenExpensePersistSchema(
            name="Child 1",
            type=CategoryTypeEnum.ENTERTAINMENT,
            amount=50.00,
            description="Child Description",
        )

        category = MagicMock(spec=Category)
        category.id = uuid4()
        category.description = "Child Description"

        expense_child = MagicMock(spec=Expense)
        expense_child.id = uuid4()

        service = ExpenseService(repository=expense_repository_mock)
        service.category_service = AsyncMock(spec=CategoryService)
        service.category_service.persist = AsyncMock(return_value=category)
        service.persist = AsyncMock(return_value=expense_child)

        await service.persist_children(
            parent=parent,
            children=[child_payload],
            reference_day=10,
            reference_year=2024,
            reference_month=3,
        )

        service.category_service.persist.assert_called_once()
        call_kwargs = service.category_service.persist.call_args[1]
        assert call_kwargs["with_throw"] is False

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_children_category_schema_without_description(
        expense_repository_mock,
    ):
        """Test that category is created with child name when description is empty"""
        parent = MagicMock(spec=Expense)
        parent.finance = MagicMock(spec=Finance)
        parent.account = MagicMock(spec=Account)
        parent.allocation = MagicMock(spec=Allocation)

        child_payload = PayloadFinanceChildrenExpensePersistSchema(
            name="Child Name",
            type=CategoryTypeEnum.ENTERTAINMENT,
            amount=50.00,
            description="",
        )

        category = MagicMock(spec=Category)
        category.id = uuid4()
        category.description = "Child Name"

        expense_child = MagicMock(spec=Expense)
        expense_child.id = uuid4()

        service = ExpenseService(repository=expense_repository_mock)
        service.category_service = AsyncMock(spec=CategoryService)
        service.category_service.persist = AsyncMock(return_value=category)
        service.persist = AsyncMock(return_value=expense_child)

        await service.persist_children(
            parent=parent,
            children=[child_payload],
            reference_day=10,
            reference_year=2024,
            reference_month=3,
        )

        service.category_service.persist.assert_called_once()
        call_kwargs = service.category_service.persist.call_args[1]
        payload = call_kwargs["payload"]
        assert payload.description == "Child Name"

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_children_category_schema_with_description(
        expense_repository_mock,
    ):
        """Test that category is created with description when provided"""
        parent = MagicMock(spec=Expense)
        parent.finance = MagicMock(spec=Finance)
        parent.account = MagicMock(spec=Account)
        parent.allocation = MagicMock(spec=Allocation)

        child_payload = PayloadFinanceChildrenExpensePersistSchema(
            name="Child Name",
            type=CategoryTypeEnum.ENTERTAINMENT,
            amount=50.00,
            description="Custom Description",
        )

        category = MagicMock(spec=Category)
        category.id = uuid4()
        category.description = "Custom Description"

        expense_child = MagicMock(spec=Expense)
        expense_child.id = uuid4()

        service = ExpenseService(repository=expense_repository_mock)
        service.category_service = AsyncMock(spec=CategoryService)
        service.category_service.persist = AsyncMock(return_value=category)
        service.persist = AsyncMock(return_value=expense_child)

        await service.persist_children(
            parent=parent,
            children=[child_payload],
            reference_day=10,
            reference_year=2024,
            reference_month=3,
        )

        service.category_service.persist.assert_called_once()
        call_kwargs = service.category_service.persist.call_args[1]
        payload = call_kwargs["payload"]
        assert payload.description == "Custom Description"

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_children_expense_called_with_correct_params(
        expense_repository_mock,
    ):
        """Test that persist is called with correct parameters"""
        parent = MagicMock(spec=Expense)
        parent.finance = MagicMock(spec=Finance)
        parent.account = MagicMock(spec=Account)
        parent.allocation = MagicMock(spec=Allocation)

        child_payload = PayloadFinanceChildrenExpensePersistSchema(
            name="Child 1",
            type=CategoryTypeEnum.ENTERTAINMENT,
            amount=75.50,
            description="Test Description",
        )

        category = MagicMock(spec=Category)
        category.id = uuid4()
        category.description = "Test Description"

        expense_child = MagicMock(spec=Expense)
        expense_child.id = uuid4()

        service = ExpenseService(repository=expense_repository_mock)
        service.category_service = AsyncMock(spec=CategoryService)
        service.category_service.persist = AsyncMock(return_value=category)
        service.persist = AsyncMock(return_value=expense_child)

        await service.persist_children(
            parent=parent,
            children=[child_payload],
            reference_day=15,
            reference_year=2024,
            reference_month=6,
        )

        service.persist.assert_called_once()
        call_kwargs = service.persist.call_args[1]
        assert call_kwargs["account"] == parent.account
        assert call_kwargs["finance"] == parent.finance
        assert call_kwargs["category"] == category
        assert call_kwargs["allocation"] == parent.allocation
        assert call_kwargs["description"] == category.description
        assert call_kwargs["reference_day"] == 15
        assert call_kwargs["reference_year"] == 2024
        assert call_kwargs["with_throw"] is False

        months = call_kwargs["months"]
        assert len(months) == 1
        assert months[0].amount == 75.50
        assert months[0].reference_month == 6

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_children_appends_all_expenses(
        expense_repository_mock,
        expense_persist_children,
    ):
        """Test that all created expenses are appended to the return list"""
        parent = MagicMock(spec=Expense)
        parent.finance = MagicMock(spec=Finance)
        parent.account = MagicMock(spec=Account)
        parent.allocation = MagicMock(spec=Allocation)

        created_expenses = [MagicMock(spec=Expense) for _ in range(5)]
        for exp in created_expenses:
            exp.id = uuid4()

        service = ExpenseService(repository=expense_repository_mock)
        service.category_service = AsyncMock(spec=CategoryService)
        service.category_service.persist = AsyncMock(
            return_value=MagicMock(spec=Category, description="Test")
        )
        service.persist = AsyncMock(side_effect=created_expenses)

        result = await service.persist_children(
            parent=parent,
            children=expense_persist_children,
            reference_day=10,
            reference_year=2024,
            reference_month=3,
        )

        assert len(result) == 5
        for i, expense in enumerate(created_expenses):
            assert result[i] == expense

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_children_uses_parent_finance_and_account(
        expense_repository_mock,
    ):
        """Test that persist_children uses parent's finance and account"""
        finance = MagicMock(spec=Finance)
        finance.id = uuid4()

        account = MagicMock(spec=Account)
        account.id = uuid4()

        allocation = MagicMock(spec=Allocation)
        allocation.id = uuid4()

        parent = MagicMock(spec=Expense)
        parent.finance = finance
        parent.account = account
        parent.allocation = allocation

        child_payload = PayloadFinanceChildrenExpensePersistSchema(
            name="Child 1",
            type=CategoryTypeEnum.ENTERTAINMENT,
            amount=50.00,
            description="Description",
        )

        category = MagicMock(spec=Category)
        category.id = uuid4()
        category.description = "Description"

        expense_child = MagicMock(spec=Expense)
        expense_child.id = uuid4()

        service = ExpenseService(repository=expense_repository_mock)
        service.category_service = AsyncMock(spec=CategoryService)
        service.category_service.persist = AsyncMock(return_value=category)
        service.persist = AsyncMock(return_value=expense_child)

        await service.persist_children(
            parent=parent,
            children=[child_payload],
            reference_day=10,
            reference_year=2024,
            reference_month=3,
        )

        call_kwargs = service.persist.call_args[1]
        assert call_kwargs["finance"] == finance
        assert call_kwargs["account"] == account
        assert call_kwargs["allocation"] == allocation

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_children_passes_reference_values_correctly(
        expense_repository_mock,
    ):
        """Test that reference_day, reference_year, and reference_month are passed correctly"""
        parent = MagicMock(spec=Expense)
        parent.finance = MagicMock(spec=Finance)
        parent.account = MagicMock(spec=Account)
        parent.allocation = MagicMock(spec=Allocation)

        child_payload = PayloadFinanceChildrenExpensePersistSchema(
            name="Child 1",
            type=CategoryTypeEnum.ENTERTAINMENT,
            amount=50.00,
            description="Description",
        )

        category = MagicMock(spec=Category)
        category.id = uuid4()
        category.description = "Description"

        expense_child = MagicMock(spec=Expense)
        expense_child.id = uuid4()

        service = ExpenseService(repository=expense_repository_mock)
        service.category_service = AsyncMock(spec=CategoryService)
        service.category_service.persist = AsyncMock(return_value=category)
        service.persist = AsyncMock(return_value=expense_child)

        await service.persist_children(
            parent=parent,
            children=[child_payload],
            reference_day=20,
            reference_year=2023,
            reference_month=12,
        )

        call_kwargs = service.persist.call_args[1]
        assert call_kwargs["reference_day"] == 20
        assert call_kwargs["reference_year"] == 2023

        months = call_kwargs["months"]
        assert months[0].reference_month == 12
