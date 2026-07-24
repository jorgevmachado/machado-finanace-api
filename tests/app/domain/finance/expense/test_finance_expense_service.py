from datetime import date
from decimal import Decimal
from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.domain.finance.allocation.service import AllocationService
from app.domain.finance.category.schema import CategorySchema
from app.domain.finance.category.service import CategoryService
from app.domain.finance.expense.pdf_parsers.schema import ParsedPDFExpenseSchema
from app.domain.finance.expense.repository import ExpenseRepository
from app.domain.finance.expense.schema import (
    PayloadExpenseCreateSchema,
    PayloadExpenseUpdateSchema,
    PayloadExpenseListPersist,
)
from app.domain.finance.expense.service import ExpenseService
from app.domain.finance.expense_month.schema import ExpenseMonthSchema
from app.domain.finance.expense_month.service import ExpenseMonthService
from app.domain.finance.months.schema import PayloadMonthPersistSchema

from app.models import (
    Allocation,
    Category,
    Finance,
    utcnow,
    BankEnum,
    MonthStatusEnum,
)

@pytest.fixture
def expense_repository_mock():
    return AsyncMock()


@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def allocation_service_mock():
    return AsyncMock()

@pytest.fixture
def category_service_mock():
    return AsyncMock()

@pytest.fixture
def expense_month_service_mock():
    return AsyncMock()

@pytest.fixture
def expense_service_with_mocks(mock_session):
    repository = AsyncMock(spec=ExpenseRepository)
    repository.session = mock_session
    category_service = AsyncMock(spec=CategoryService)
    allocation_service = AsyncMock(spec=AllocationService)
    expense_month_service = AsyncMock(spec=ExpenseMonthService)

    return ExpenseService(
        repository=repository,
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

@pytest.fixture
def payload_months(value: float = 100.0):
    months: list[PayloadMonthPersistSchema] = []
    for i in range(1, 13):
        months.append(PayloadMonthPersistSchema(amount=value, reference_month=i))
    return months

@pytest.fixture
def expense(category, allocation):
    expense = MagicMock()
    expense.id = uuid4()
    expense.payee = "Test Payee"
    expense.months = []
    expense.payee_code = "test_payee"
    expense.category_id = category.id
    expense.category = category
    expense.description = "Test Expense"
    expense.allocation_id = allocation.id
    expense.allocation = allocation
    return expense


class TestFinanceExpenseCreateService:
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
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)

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
            months=[
                SimpleNamespace(
                    amount=Decimal("75.00"),
                    status=None,
                    reference_month=1,
                    paid_at=None,
                ),
                SimpleNamespace(
                    amount=Decimal("25.00"),
                    status=None,
                    reference_month=7,
                    paid_at=None,
                ),
            ],
        )
        expense_repository_mock.find_by.return_value = exist_expense
        expense_repository_mock.update.return_value = exist_expense
        service = ExpenseService(repository=expense_repository_mock)
        service.expense_month_service.persist_list = AsyncMock(return_value=months)
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
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
        persisted_call = service.expense_month_service.persist_list.await_args.kwargs
        persisted_months = persisted_call["months"]
        persisted_by_reference_month = {
            month.reference_month: month.amount for month in persisted_months
        }
        assert persisted_by_reference_month[1] == 175.0
        assert persisted_by_reference_month[6] == 150.0
        assert persisted_by_reference_month[7] == 25.0

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
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
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

class TestFinanceExpenseUpdateService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_update_service_with_payload_none(
            expense_repository_mock, expense
    ):
        payload = PayloadExpenseUpdateSchema(
            payee=None,
            months=None,
            category_id=None,
            allocation_id=None,
            description=None,
            reference_day=None,
            reference_year=None
        )

        service = ExpenseService(repository=expense_repository_mock)
        service.find_one = AsyncMock(return_value=expense)
        result = await service.update(
            param=str(expense.id),
            payload=payload,
            user_request="test_user"
        )
        assert result == expense

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_update_service_with_payload_allocation_not_found(
        expense_repository_mock, expense, allocation_service_mock
    ):
        payload = PayloadExpenseUpdateSchema(
            payee=None,
            months=None,
            category_id=None,
            allocation_id=uuid4(),
            description=None,
            reference_day=None,
            reference_year=None,
        )

        allocation_service_mock.find_by.return_value = None
        service = ExpenseService(repository=expense_repository_mock, allocation_service=allocation_service_mock)
        service.find_one = AsyncMock(return_value=expense)
        with pytest.raises(HTTPException) as exc_info:
            await service.update(
                param=str(expense.id), payload=payload, user_request="test_user"
            )
        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == f"Allocation with this id {payload.allocation_id} does not exist"
        allocation_service_mock.find_by.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_update_service_with_payload_allocation_changed(
        expense_repository_mock, expense, allocation_service_mock
    ):
        new_allocation = expense.allocation
        new_allocation.id = uuid4()
        payload = PayloadExpenseUpdateSchema(
            payee=None,
            months=None,
            category_id=None,
            allocation_id=new_allocation.id,
            description=None,
            reference_day=None,
            reference_year=None,
        )

        allocation_service_mock.find_by.return_value = new_allocation
        service = ExpenseService(
            repository=expense_repository_mock,
            allocation_service=allocation_service_mock,
        )
        service.find_one = AsyncMock(return_value=expense)
        service.cache_service.delete_domain = AsyncMock()
        expense_repository_mock.update.return_value = expense
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
        result = await service.update(
            param=str(expense.id), payload=payload, user_request="test_user"
        )
        assert result == expense
        allocation_service_mock.find_by.assert_awaited_once()
        expense_repository_mock.update.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_update_service_with_payload_category_not_found(
        expense_repository_mock, expense, category_service_mock
    ):
        payload = PayloadExpenseUpdateSchema(
            payee=None,
            months=None,
            category_id=uuid4(),
            allocation_id=None,
            description=None,
            reference_day=None,
            reference_year=None,
        )

        category_service_mock.find_by.return_value = None
        service = ExpenseService(
            repository=expense_repository_mock,
            category_service=category_service_mock,
        )
        service.find_one = AsyncMock(return_value=expense)
        with pytest.raises(HTTPException) as exc_info:
            await service.update(
                param=str(expense.id), payload=payload, user_request="test_user"
            )
        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == f"Category {payload.category_id} not found"
        category_service_mock.find_by.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_update_service_with_payload_category_changed(
        expense_repository_mock, expense, category_service_mock
    ):
        new_category = expense.category
        new_category.id = uuid4()
        payload = PayloadExpenseUpdateSchema(
            payee=None,
            months=None,
            category_id=new_category.id,
            allocation_id=None,
            description=None,
            reference_day=None,
            reference_year=None,
        )

        category_service_mock.find_by.return_value = new_category
        service = ExpenseService(
            repository=expense_repository_mock,
            category_service=category_service_mock,
        )
        service.find_one = AsyncMock(return_value=expense)
        service.cache_service.delete_domain = AsyncMock()
        expense_repository_mock.update.return_value = expense
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
        result = await service.update(
            param=str(expense.id), payload=payload, user_request="test_user"
        )
        assert result == expense
        category_service_mock.find_by.assert_awaited_once()
        expense_repository_mock.update.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_update_service_with_payload_payee_with_error(
        expense_repository_mock, expense
    ):
        
        payload = PayloadExpenseUpdateSchema(
            payee="New Payee",
            months=None,
            category_id=None,
            allocation_id=None,
            description=None,
            reference_day=None,
            reference_year=None,
        )

        service = ExpenseService(
            repository=expense_repository_mock,
        )
        other_expense = expense
        other_expense.id = uuid4()
        service.find_one = AsyncMock(return_value=expense)
        service.find_by = AsyncMock(return_value=SimpleNamespace(id=uuid4()))
        with pytest.raises(HTTPException) as exc_info:
            await service.update(
                param=str(expense.id), payload=payload, user_request="test_user"
            )
        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == f"Expense with payee {payload.payee} already exists"

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_update_service_with_payload_payee_changed(
        expense_repository_mock, expense
    ):

        payload = PayloadExpenseUpdateSchema(
            payee="New Payee",
            months=None,
            category_id=None,
            allocation_id=None,
            description=None,
            reference_day=None,
            reference_year=None,
        )

        service = ExpenseService(
            repository=expense_repository_mock,
        )
        other_expense = expense
        other_expense.id = uuid4()
        service.find_one = AsyncMock(return_value=expense)
        service.find_by = AsyncMock(return_value=None)
        service.cache_service.delete_domain = AsyncMock()
        expense_repository_mock.update.return_value = expense
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
        result = await service.update(
            param=str(expense.id), payload=payload, user_request="test_user"
        )
        assert result.payee == payload.payee
        expense_repository_mock.update.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_update_service_with_payload_description_changed(
        expense_repository_mock, expense
    ):

        payload = PayloadExpenseUpdateSchema(
            payee=None,
            months=None,
            category_id=None,
            allocation_id=None,
            description="New Description",
            reference_day=None,
            reference_year=None,
        )

        service = ExpenseService(
            repository=expense_repository_mock,
        )
        other_expense = expense
        other_expense.id = uuid4()
        service.find_one = AsyncMock(return_value=expense)
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
        expense_repository_mock.update.return_value = expense
        result = await service.update(
            param=str(expense.id), payload=payload, user_request="test_user"
        )
        assert result.description == payload.description
        expense_repository_mock.update.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_update_service_with_payload_parent_with_error(
        expense_repository_mock, expense
    ):

        payload = PayloadExpenseUpdateSchema(
            payee=None,
            months=None,
            parent_id=uuid4(),
            category_id=None,
            allocation_id=None,
            description=None,
            reference_day=None,
            reference_year=None,
        )

        service = ExpenseService(
            repository=expense_repository_mock,
        )
        other_expense = expense
        other_expense.id = uuid4()
        service.find_one = AsyncMock(return_value=expense)
        service.find_by = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc_info:
            await service.update(
                param=str(expense.id), payload=payload, user_request="test_user"
            )
        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Parent expense with id {payload.parent_id} does not exist"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_update_service_with_payload_parent_changed(
        expense_repository_mock, expense
    ):

        parent = expense
        parent.id = uuid4()
        
        payload = PayloadExpenseUpdateSchema(
            payee=None,
            months=None,
            parent_id=parent.id,
            category_id=None,
            allocation_id=None,
            description=None,
            reference_day=None,
            reference_year=None,
        )

        service = ExpenseService(
            repository=expense_repository_mock,
        )
        other_expense = expense
        other_expense.id = uuid4()
        service.find_one = AsyncMock(return_value=expense)
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
        expense_repository_mock.update.return_value = expense
        service.find_by = AsyncMock(return_value=parent)
        result = await service.update(
            param=str(expense.id), payload=payload, user_request="test_user"
        )
        assert result.parent_id == payload.parent_id
        expense_repository_mock.update.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_update_service_with_payload_months_changed(
        expense_repository_mock,
        expense,
        payload_months,
        expense_month_service_mock,
    ):

        new_months = payload_months[:3]

        payload = PayloadExpenseUpdateSchema(
            months=new_months,
            payee=None,
            allocation_id=None,
            description=None,
            reference_year=None,
        )

        service = ExpenseService(
            repository=expense_repository_mock,
            expense_month_service=expense_month_service_mock,
        )
        service.find_one = AsyncMock(return_value=expense)
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
        expense_month_service_mock.persist_list = AsyncMock(return_value=new_months)
        expense_repository_mock.update.return_value = expense
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)

        result = await service.update(
            param=str(expense.id),
            payload=payload,
            user_request="test_user",
        )
        assert result == expense
        expense_month_service_mock.persist_list.assert_awaited_once()
        expense_repository_mock.update.assert_awaited_once()


class TestFinanceExpenseUploadService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_upload_service_allocation_not_found(
        finance,expense_repository_mock,
    ):
        service = ExpenseService(repository=expense_repository_mock)
        service.allocation_service.find_by = AsyncMock(return_value=None)
        file = SimpleNamespace(content_type="application/pdf", read=AsyncMock())

        with pytest.raises(HTTPException) as exc_info:
            await service.upload(
                file=file,
                bank=BankEnum.ITAU,
                finance=finance,
                allocation_id=str(uuid4()),
                reference_year=2026,
                reference_month=7,
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert "Allocation with this id" in exc_info.value.detail

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_upload_service_invalid_content_type(
            finance,
        expense_repository_mock,
        allocation,
    ):
        service = ExpenseService(repository=expense_repository_mock)
        service.allocation_service.find_by = AsyncMock(return_value=allocation)
        file = SimpleNamespace(content_type="text/plain", read=AsyncMock())

        with pytest.raises(HTTPException) as exc_info:
            await service.upload(
                file=file,
                bank=BankEnum.ITAU,
                finance=finance,
                allocation_id=str(allocation.id),
                reference_year=2026,
                reference_month=7,
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "File must be a PDF"

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_upload_service_success(
            finance,
        expense_repository_mock,
        allocation,
        monkeypatch,
    ):
        expenses: list[ParsedPDFExpenseSchema] = [
            ParsedPDFExpenseSchema(
                date=date(2026, 7, 1),
                payee="Payee One",
                amount=100.0,
                category="OTHERS",
                reference_month=7,
                current_installment=1,
                total_of_installments=1,
                all_installments_paid=False
            ),
            ParsedPDFExpenseSchema(
                date=date(2026, 7, 2),
                payee="Payee Two",
                amount=100.0,
                category="OTHERS",
                reference_month=7,
                current_installment=1,
                total_of_installments=1,
                all_installments_paid=False
            ),
        ]
        expense_with_category = SimpleNamespace(
            id=uuid4(),
            payee="Payee Two",
            payee_code="payee_two",
            category=SimpleNamespace(id=uuid4(), name="Category Two"),
        )
        parsed_allocation = SimpleNamespace(
            id=allocation.id,
            name="Default Allocation",
            expenses=[],
            name_code="default_allocation",
            is_active=True,
            account_id=uuid4(),
            description="Default allocation",
            allocation_contributions=[],
            created_at=utcnow(),
            updated_at=None,
            deleted_at=None,
        )
        parsed_result = SimpleNamespace(
            bank=BankEnum.ITAU,
            error=False,
            message="Create Successfully!",
            expenses=expenses,
            allocation=parsed_allocation,
            bill_total=200.0,
            bill_due_date=date(2026, 7, 10),
            date_of_issue=date(2026, 7, 1),
            reference_year=2026,
            reference_month=7,
            previous_bill_total=100.0,
            previous_bill_due_date=date(2026, 6, 10),
        )

        parent_category_schema = CategorySchema(
            id=uuid4(),
            name="Credit Card",
            name_code="credit_card",
            finance_id=finance.id,
            description="Category Credit Card generated from file upload",
            created_at=utcnow(),
            updated_at=None,
            deleted_at=None,
        )
        
        category_schema = CategorySchema(
            id=uuid4(),
            name="OTHERS",
            name_code="others",
            finance_id=finance.id,
            description="Default category",
            created_at=utcnow(),
            updated_at=None,
            deleted_at=None,
        )
        
        service = ExpenseService(repository=expense_repository_mock)
        service.allocation_service.find_by = AsyncMock(return_value=allocation)
        service.find_by = AsyncMock(side_effect=[None, expense_with_category])
        service.upload_validate_category = AsyncMock(side_effect=[parent_category_schema, category_schema, category_schema])
        file = SimpleNamespace(content_type="application/pdf", read=AsyncMock(return_value=b"pdf"))

        captured = {}

        def _fake_parse_pdf(file, bank, allocation, reference_year=None, reference_month=None):
            captured["file"] = file
            captured["bank"] = bank
            captured["allocation"] = allocation
            captured["reference_year"] = reference_year
            captured["reference_month"] = reference_month
            return parsed_result

        monkeypatch.setattr("app.domain.finance.expense.service.parse_pdf", _fake_parse_pdf)

        result = await service.upload(
            file=file,
            bank=BankEnum.ITAU,
            finance=finance,
            allocation_id=str(allocation.id),
            reference_year=2026,
            reference_month=7,
        )

        assert result.bank == BankEnum.ITAU
        assert result.error is False
        assert len(result.expenses) == 2
        assert result.expenses[0].category.name == "OTHERS"
        assert result.expenses[1].category.name == "OTHERS"
        assert service.upload_validate_category.await_count == 3
        assert captured == {
            "file": b"pdf",
            "bank": BankEnum.ITAU,
            "allocation": allocation,
            "reference_year": 2026,
            "reference_month": 7,
        }

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_upload_service_with_error_when_parsed_error(
        expense_repository_mock,
        allocation,
        monkeypatch,
            finance
    ):
        expected = SimpleNamespace(bank=BankEnum.ITAU, error=True, expenses=[], message="Error parsing PDF")
        service = ExpenseService(repository=expense_repository_mock)
        service.allocation_service.find_by = AsyncMock(return_value=allocation)
        file = SimpleNamespace(
            content_type="application/pdf", read=AsyncMock(return_value=b"pdf")
        )

        captured = {}

        def _fake_parse_pdf(
            file, bank, allocation, reference_year=None, reference_month=None
        ):
            captured["file"] = file
            captured["bank"] = bank
            captured["allocation"] = allocation
            captured["reference_year"] = reference_year
            captured["reference_month"] = reference_month
            return expected

        monkeypatch.setattr(
            "app.domain.finance.expense.service.parse_pdf", _fake_parse_pdf
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.upload(
                file=file,
                bank=BankEnum.ITAU,
                finance=finance,
                allocation_id=str(allocation.id),
                reference_year=2026,
                reference_month=7,
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "Error parsing PDF"
        
    @staticmethod
    def test_finance_expense_service_from_session():
        session = AsyncMock()
        service = ExpenseService.from_session(session)
        assert isinstance(service, ExpenseService)


class TestFinanceExpenseUploadValidateCategoryService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_upload_validate_category_with_category(
        expense_repository_mock,
        finance,
    ):
        category = MagicMock(spec=Category)
        category.id = uuid4()
        category.name = "TRANSPORT"
        category.name_code = "transport"
        category.finance_id = finance.id
        category.description = "Transport category"
        category.created_at = utcnow()
        category.updated_at = None
        category.deleted_at = None

        service = ExpenseService(repository=expense_repository_mock)
        service.category_service.find_by = AsyncMock()
        service.category_service.persist = AsyncMock()

        result = await service.upload_validate_category(
            finance=finance,
            category=category,
        )

        assert result.name == "TRANSPORT"
        assert result.finance_id == finance.id
        service.category_service.find_by.assert_not_awaited()
        service.category_service.persist.assert_not_awaited()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_upload_validate_category_without_category_with_category_name(
        expense_repository_mock,
        finance,
    ):
        generated_category = MagicMock(spec=Category)
        generated_category.id = uuid4()
        generated_category.name = "SUPERMARKET"
        generated_category.name_code = "supermarket"
        generated_category.finance_id = finance.id
        generated_category.description = "Category SUPERMARKET generated from file upload"
        generated_category.created_at = utcnow()
        generated_category.updated_at = None
        generated_category.deleted_at = None

        service = ExpenseService(repository=expense_repository_mock)
        service.category_service.find_by = AsyncMock()
        service.category_service.persist = AsyncMock(return_value=generated_category)

        result = await service.upload_validate_category(
            finance=finance,
            category_name="SUPERMARKET",
        )

        assert result.name == "SUPERMARKET"
        assert result.finance_id == finance.id
        service.category_service.find_by.assert_not_awaited()
        service.category_service.persist.assert_awaited_once_with(
            name="SUPERMARKET",
            finance=finance,
            description="Category SUPERMARKET generated from file upload",
            with_throw=False,
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_expense_upload_validate_category_without_category_and_without_category_name(
        expense_repository_mock,
        finance,
    ):
        default_category = MagicMock(spec=Category)
        default_category.id = uuid4()
        default_category.name = "OTHERS"
        default_category.name_code = "others"
        default_category.finance_id = finance.id
        default_category.description = "Category OTHERS generated from file upload"
        default_category.created_at = utcnow()
        default_category.updated_at = None
        default_category.deleted_at = None

        service = ExpenseService(repository=expense_repository_mock)
        service.category_service.find_by = AsyncMock()
        service.category_service.persist = AsyncMock(return_value=default_category)

        result = await service.upload_validate_category(finance=finance)

        assert result.name == "OTHERS"
        assert result.finance_id == finance.id
        service.category_service.find_by.assert_not_awaited()
        service.category_service.persist.assert_awaited_once_with(
            name="OTHERS",
            finance=finance,
            description="Category OTHERS generated from file upload",
            with_throw=False,
        )
        
class TestFinanceExpensePersistList:
    @staticmethod
    @pytest.mark.asyncio
    async def test_expense_persist_list_without_parent(
        expense_repository_mock,
        finance,
        category,
        allocation,
    ):
        current_year = utcnow().year

        expense_payload_create = PayloadExpenseCreateSchema(
            payee="Test Payee",
            months=[],
            category_id=category.id,
            allocation_id=allocation.id,
            description="Test Expense",
            reference_day=10,
            reference_year=current_year,
        )
        
        payload = PayloadExpenseListPersist(
            expenses=[expense_payload_create],
            reference_month=1
        )
        
        saved_expenses = []
        for expense_payload in payload.expenses:
            saved_expense = SimpleNamespace(
                id=uuid4(),
                payee=expense_payload.payee,
                category_id=expense_payload.category_id,
                description=expense_payload.description,
                allocation_id=expense_payload.allocation_id,
            )
            saved_expenses.append(saved_expense)
            expense_repository_mock.save.return_value = saved_expense

        service = ExpenseService(repository=expense_repository_mock)
        service.allocation_service.find_by = AsyncMock(return_value=allocation)
        service.category_service.find_by = AsyncMock(return_value=category)
        service.find_by = AsyncMock(side_effect=[None, saved_expenses[0]])
        service.expense_month_service.persist_list = AsyncMock(return_value=[])
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)

        result = await service.persist_list(finance=finance, payload=payload)
        assert result == saved_expenses

    @staticmethod
    @pytest.mark.asyncio
    async def test_expense_persist_list_with_parent(
        expense_repository_mock,
        finance,
        category,
        allocation,
    ):
        current_datetime = utcnow()
        current_year = current_datetime.year
        current_month = current_datetime.month
        
        parent_expense_id = uuid4()
        parent_expense_payload_create = PayloadExpenseCreateSchema(
            payee="Parent Payee",
            months=[],
            category_id=category.id,
            allocation_id=allocation.id,
            description="Parent Expense",
            reference_day=10,
            reference_year=current_year,
        )
        expense_id = uuid4()    
        parent_payload_months: list[PayloadMonthPersistSchema] = []
        payload_months: list[PayloadMonthPersistSchema] = []
        expense_months: list[ExpenseMonthSchema] = []
        parent_expense_months: list[ExpenseMonthSchema] = []
        for i in range(1, 13):
            status = MonthStatusEnum.PAID if i < current_month else MonthStatusEnum.PENDING
            amount = 100.00
            reference_month = i
            payload_months.append(PayloadMonthPersistSchema(
                amount=amount,
                status=status,
                reference_month=reference_month,
            ))
            expense_months.append(ExpenseMonthSchema(
                id=uuid4(),
                amount=amount,
                status=status,
                expense_id=expense_id,
                reference_month=reference_month,
                reference_year=current_year,
                created_at=utcnow(),
            ))
            parent_payload_months.append(PayloadMonthPersistSchema(
                amount=amount,
                status=status,
                reference_month=reference_month,
            ))
            parent_expense_months.append(ExpenseMonthSchema(
                id=uuid4(),
                amount=amount,
                status=status,
                expense_id=parent_expense_id,
                reference_month=reference_month,
                reference_year=current_year,
                created_at=utcnow(),
            ))

        expense_payload_create = PayloadExpenseCreateSchema(
            payee="Test Payee",
            months=payload_months,
            category_id=category.id,
            allocation_id=allocation.id,
            description="Test Expense",
            reference_day=10,
            reference_year=current_year,
        )

        saved_parent_expense = SimpleNamespace(
            id=parent_expense_id,
            payee=parent_expense_payload_create.payee,
            months=parent_expense_months,
            category_id=parent_expense_payload_create.category_id,
            description=parent_expense_payload_create.description,
            allocation_id=parent_expense_payload_create.allocation_id,
        )
        
        saved_children_expense = SimpleNamespace(
            id=expense_id,
            payee=expense_payload_create.payee,
            months=expense_months,
            category_id=expense_payload_create.category_id,
            description=expense_payload_create.description,
            allocation_id=expense_payload_create.allocation_id,
        )

        payload = PayloadExpenseListPersist(parent=parent_expense_payload_create, expenses=[expense_payload_create], reference_month=1)

        
        expense_repository_mock.save.return_value = saved_parent_expense

        expense_repository_mock.save.return_value = saved_children_expense

        service = ExpenseService(repository=expense_repository_mock)

        service.allocation_service.find_by = AsyncMock(side_effect=[allocation, allocation])

        service.category_service.find_by = AsyncMock(side_effect=[category, category])

        service.find_by = AsyncMock(side_effect=[None, saved_parent_expense, None, saved_children_expense])
        service.cache_service.delete_with_parent_cache = AsyncMock(return_value=None)
        result = await service.persist_list(finance=finance, payload=payload)
        assert result == [saved_parent_expense]