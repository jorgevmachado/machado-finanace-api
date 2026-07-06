from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


import pytest
from fastapi import HTTPException

from app.domain.finance.months.schema import PayloadMonthPersistSchema
from app.domain.finance.income.schema import PayloadIncomePersistSchema
from app.domain.finance.persist_schema import (
    PayloadPersistSchema,
    PayloadPersistAllocationSchema,
    PayloadPersistCategorySchema,
    PayloadPersistParentExpenseSchema,
    PayloadPersistChildrenCategorySchema,
    PayloadPersistChildrenExpenseSchema,
)
from app.domain.finance.service import FinanceService
from app.models import Account, Allocation, Category, Finance, AccountTypeEnum, utcnow, Income, Expense


@pytest.fixture
def account_service_mock():
    return AsyncMock()

@pytest.fixture
def income_service_mock():
    return AsyncMock()

@pytest.fixture
def allocation_service_mock():
    return AsyncMock()

@pytest.fixture
def category_service_mock():
    return AsyncMock()

@pytest.fixture
def expense_service_mock():
    return AsyncMock()

@pytest.fixture
def allocation_contribution_service_mock():
    return AsyncMock()

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
    account.current_balance = 0
    return account

@pytest.fixture()
def income():
    income = MagicMock(spec=Income)
    income.id = uuid4()
    income.source = "Test Income"
    income.description = "Test Income Description"
    return income

@pytest.fixture
def allocation():
    allocation = MagicMock(spec=Allocation)
    allocation.id = uuid4()
    allocation.name = "Test Allocation"
    allocation.description = "Test Allocation Description"
    return allocation

@pytest.fixture
def category():
    category = MagicMock(spec=Category)
    category.id = uuid4()
    category.name = "Test Category"
    category.description = "Test Category Description"   
    return category

@pytest.fixture
def expense():
    expense = MagicMock(spec=Expense)    
    expense.id = uuid4()
    expense.payee = "Test Payee"
    expense.description = "Test Expense Description"   
    return expense

@pytest.fixture
def payload_months(value: float = 100.0):
    months: list[PayloadMonthPersistSchema] = []
    for i in range(1, 13):
        months.append(PayloadMonthPersistSchema(
            amount=value,
            reference_month=i
        ))
    return months


@pytest.fixture
def finance_repository_mock() -> AsyncMock:
    return AsyncMock()


class TestFinanceServiceFromSession:
    @staticmethod
    @pytest.mark.asyncio
    async def test_from_session_builds_service() -> None:
        service = FinanceService.from_session(AsyncMock())
        assert isinstance(service, FinanceService)


class TestFinanceOnboardingService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_onboarding_service_has_onboarding(
        finance_repository_mock: AsyncMock,
    ):
        finance = SimpleNamespace(id=uuid4())
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=finance.id)
        )

        service = FinanceService(repository=finance_repository_mock)

        with pytest.raises(HTTPException) as exc_info:
            await service.onboard(current_user=current_user)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail == f"User {current_user.username} already onboarded"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_onboarding_service_success_onboarding(
        finance_repository_mock: AsyncMock,
    ):
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=None
        )
        finance = SimpleNamespace(id=uuid4(), user_id=current_user.id)
        finance_repository_mock.create.return_value = finance
        finance_repository_mock.save.return_value = SimpleNamespace(
            id=finance.id, user_id=current_user.id
        )

        service = FinanceService(repository=finance_repository_mock)
        result = await service.onboard(current_user=current_user)
        assert result == finance

class TestFinancePersistService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_persist_with_empty_payloads(
            finance_repository_mock,
            account_service_mock,
            income_service_mock,
            allocation_service_mock,
            category_service_mock,
            expense_service_mock,
            allocation_contribution_service_mock,
            finance
    ):
        payloads: list[PayloadPersistSchema] = []
        service = FinanceService(
            repository=finance_repository_mock,
            account_service=account_service_mock,
            income_service=income_service_mock,
            allocation_service=allocation_service_mock,
            category_service=category_service_mock,
            expense_service=expense_service_mock,
            allocation_contribution_service=allocation_contribution_service_mock
        )
        result = await service.persist(finance=finance, payloads=payloads)
        assert result.accounts == 0
        assert result.incomes == 0
        assert result.allocations == 0
        assert result.expenses == 0
        assert result.categories == 0

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_persist_with_only_accounts_in_payloads(
            finance_repository_mock,
            account_service_mock,
            income_service_mock,
            allocation_service_mock,
            category_service_mock,
            expense_service_mock,
            allocation_contribution_service_mock,
             finance,
            account
    ):
        
        reference_year = utcnow().year
        reference_day = 10
        account_bank = account        
        account_bank.type = AccountTypeEnum.BANK
        account_bank.name = "Test Account Bank"        
        account_bank.initial_balance = 1000
        
        account_cash = account
        account_cash.id = uuid4()
        account_cash.type = AccountTypeEnum.CASH        
        account_cash.name = "Test Account Cash"
        account_cash.initial_balance = 2000
        
        account_other = account
        account_other.id = uuid4()
        account_other.type = AccountTypeEnum.OTHER        
        account_other.name = "Test Account Other"
        account_other.initial_balance = 3000


        account_investment = account
        account_investment.id = uuid4()
        account_investment.type = AccountTypeEnum.INVESTMENT
        account_investment.name = "Test Account Investment"
        account_investment.initial_balance = 4000
    
        payloads: list[PayloadPersistSchema] = [
            PayloadPersistSchema(
                name=account_bank.name,
                type=AccountTypeEnum.BANK,
                incomes=[],
                allocations=[],
                reference_day=reference_day,
                reference_year=reference_year,
                initial_balance=account_bank.initial_balance,
            ),
            PayloadPersistSchema(
                name=account_cash.name,
                type=account_cash.type,
                incomes=[],
                allocations=[],
                reference_day=reference_day,
                reference_year=reference_year,
                initial_balance=account_cash.initial_balance,
            ),
            PayloadPersistSchema(
                name=account_other.name,
                type=account_other.type,
                incomes=[],
                allocations=[],
                reference_day=reference_day,
                reference_year=reference_year,
                initial_balance=account_other.initial_balance,
            ),
            PayloadPersistSchema(
                name=account_investment.name,
                type=account_investment.type,
                incomes=[],
                allocations=[],
                reference_day=reference_day,
                reference_year=reference_year,
                initial_balance=account_investment.initial_balance,
            ),
        ]
        service = FinanceService(
            repository=finance_repository_mock,
            account_service=account_service_mock,
            income_service=income_service_mock,
            allocation_service=allocation_service_mock,
            category_service=category_service_mock,
            expense_service=expense_service_mock,
            allocation_contribution_service=allocation_contribution_service_mock,
        )
        account_service_mock.persist.side_effect = [account_bank, account_cash, account_other, account_investment]
        
        result = await service.persist(finance=finance, payloads=payloads)
        assert result.accounts == 4
        assert result.incomes == 0
        assert result.allocations == 0
        assert result.expenses == 0
        assert result.categories == 0
        account_service_mock.persist.assert_awaited()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_persist_with_incomes_in_account(
        finance_repository_mock,
        account_service_mock,
        income_service_mock,
        allocation_service_mock,
        category_service_mock,
        expense_service_mock,
        allocation_contribution_service_mock,
        finance,
        account,
        income,
        payload_months,
    ):

        reference_year = utcnow().year
        reference_day = 10
        account_bank = account
        account_bank.type = AccountTypeEnum.BANK
        account_bank.name = "Test Account Bank"
        account_bank.initial_balance = 1000

        income.account_id = account_bank.id

        payload_incomes: list[PayloadIncomePersistSchema] = [
            PayloadIncomePersistSchema(
                months=payload_months,
                source=income.source,
                description=income.description,
            )
        ]

        payloads: list[PayloadPersistSchema] = [
            PayloadPersistSchema(
                name=account_bank.name,
                type=AccountTypeEnum.BANK,
                incomes=payload_incomes,
                allocations=[],
                reference_day=reference_day,
                reference_year=reference_year,
                initial_balance=account_bank.initial_balance,
            ),
        ]
        service = FinanceService(
            repository=finance_repository_mock,
            account_service=account_service_mock,
            income_service=income_service_mock,
            allocation_service=allocation_service_mock,
            category_service=category_service_mock,
            expense_service=expense_service_mock,
            allocation_contribution_service=allocation_contribution_service_mock,
        )
        account_service_mock.persist.return_value=account_bank
        income_service_mock.persist_list.return_value=[income]
        result = await service.persist(finance=finance, payloads=payloads)
        assert result.accounts == 1
        assert result.incomes == 1
        assert result.allocations == 0
        assert result.expenses == 0
        assert result.categories == 0
        account_service_mock.persist.assert_awaited_once()
        income_service_mock.persist_list.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_persist_with_allocations_with_categories_empty_in_account(
        finance_repository_mock,
        account_service_mock,
        income_service_mock,
        allocation_service_mock,
        category_service_mock,
        expense_service_mock,
        allocation_contribution_service_mock,
        finance,
        account,
        allocation,
    ):

        reference_year = utcnow().year
        reference_day = 10
        account_bank = account
        account_bank.type = AccountTypeEnum.BANK
        account_bank.name = "Test Account Bank"
        account_bank.initial_balance = 1000

        allocation.account_id = account_bank.id

        payload_allocations: list[PayloadPersistAllocationSchema] = [
            PayloadPersistAllocationSchema(
                name=allocation.name,
                description=allocation.description,
            )
        ]

        payloads: list[PayloadPersistSchema] = [
            PayloadPersistSchema(
                name=account_bank.name,
                type=AccountTypeEnum.BANK,
                incomes=[],
                allocations=payload_allocations,
                reference_day=reference_day,
                reference_year=reference_year,
                initial_balance=account_bank.initial_balance,
            ),
        ]
        service = FinanceService(
            repository=finance_repository_mock,
            account_service=account_service_mock,
            income_service=income_service_mock,
            allocation_service=allocation_service_mock,
            category_service=category_service_mock,
            expense_service=expense_service_mock,
            allocation_contribution_service=allocation_contribution_service_mock,
        )
        account_service_mock.persist.return_value = account_bank
        allocation_service_mock.persist.return_value = allocation
        service.account_service.persist = AsyncMock(return_value=account_bank)
        result = await service.persist(finance=finance, payloads=payloads)
        assert result.accounts == 1
        assert result.incomes == 0
        assert result.allocations == 1
        assert result.expenses == 0
        assert result.categories == 0
        account_service_mock.persist.assert_awaited_once()
        allocation_service_mock.persist.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_persist_with_allocations_with_categories_with_expenses_empty_in_account(
        finance_repository_mock,
        account_service_mock,
        income_service_mock,
        allocation_service_mock,
        category_service_mock,
        expense_service_mock,
        allocation_contribution_service_mock,
        finance,
        account,
        allocation,
        category,
    ):

        reference_year = utcnow().year
        reference_day = 10
        account_bank = account
        account_bank.type = AccountTypeEnum.BANK
        account_bank.name = "Test Account Bank"
        account_bank.initial_balance = 1000

        allocation.account_id = account_bank.id
        category.finance_id = finance.id


        payload_categories: list[PayloadPersistCategorySchema] = [
            PayloadPersistCategorySchema(
                name=category.name,
                description=category.description
            )
        ]
        payload_allocations: list[PayloadPersistAllocationSchema] = [
            PayloadPersistAllocationSchema(
                name=allocation.name,
                categories=payload_categories,
                description=allocation.description,
            )
        ]

        payloads: list[PayloadPersistSchema] = [
            PayloadPersistSchema(
                name=account_bank.name,
                type=AccountTypeEnum.BANK,
                incomes=[],
                allocations=payload_allocations,
                reference_day=reference_day,
                reference_year=reference_year,
                initial_balance=account_bank.initial_balance,
            ),
        ]
        service = FinanceService(
            repository=finance_repository_mock,
            account_service=account_service_mock,
            income_service=income_service_mock,
            allocation_service=allocation_service_mock,
            category_service=category_service_mock,
            expense_service=expense_service_mock,
            allocation_contribution_service=allocation_contribution_service_mock,
        )
        account_service_mock.persist.return_value = account_bank
        allocation_service_mock.persist.return_value = allocation
        category_service_mock.persist.return_value = category
        service.account_service.persist = AsyncMock(return_value=account_bank)
        result = await service.persist(finance=finance, payloads=payloads)
        assert result.accounts == 1
        assert result.incomes == 0
        assert result.allocations == 1
        assert result.expenses == 0
        assert result.categories == 1
        account_service_mock.persist.assert_awaited_once()
        allocation_service_mock.persist.assert_awaited_once()
        category_service_mock.persist.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_persist_with_allocations_with_categories_with_expenses_simple_in_account(
        finance_repository_mock,
        account_service_mock,
        income_service_mock,
        allocation_service_mock,
        category_service_mock,
        expense_service_mock,
        allocation_contribution_service_mock,
        finance,
        account,
        allocation,
        category,
        expense,
        payload_months,
    ):

        reference_year = utcnow().year
        reference_day = 10
        account_bank = account
        account_bank.type = AccountTypeEnum.BANK
        account_bank.name = "Test Account Bank"
        account_bank.initial_balance = 1000

        allocation.account_id = account_bank.id
        
        category.finance_id = finance.id
        
        expense.allocation_id = allocation.id
        expense.category_id = category.id

        payload_parent_expenses: list[PayloadPersistParentExpenseSchema] = [
            PayloadPersistParentExpenseSchema(
                name=expense.payee,
                months=payload_months,
                description=expense.description
            )
        ]
        
        payload_categories: list[PayloadPersistCategorySchema] = [
            PayloadPersistCategorySchema(
                name=category.name,
                expenses=payload_parent_expenses,
                description=category.description
            )
        ]
        payload_allocations: list[PayloadPersistAllocationSchema] = [
            PayloadPersistAllocationSchema(
                name=allocation.name,
                categories=payload_categories,
                description=allocation.description,
            )
        ]

        payloads: list[PayloadPersistSchema] = [
            PayloadPersistSchema(
                name=account_bank.name,
                type=AccountTypeEnum.BANK,
                incomes=[],
                allocations=payload_allocations,
                reference_day=reference_day,
                reference_year=reference_year,
                initial_balance=account_bank.initial_balance,
            ),
        ]
        service = FinanceService(
            repository=finance_repository_mock,
            account_service=account_service_mock,
            income_service=income_service_mock,
            allocation_service=allocation_service_mock,
            category_service=category_service_mock,
            expense_service=expense_service_mock,
            allocation_contribution_service=allocation_contribution_service_mock,
        )
        account_service_mock.persist.return_value = account_bank
        allocation_service_mock.persist.return_value = allocation
        category_service_mock.persist.return_value = category
        expense_service_mock.persist.return_value = expense
        service.account_service.persist = AsyncMock(return_value=account_bank)
        result = await service.persist(finance=finance, payloads=payloads)
        assert result.accounts == 1
        assert result.incomes == 0
        assert result.allocations == 1
        assert result.expenses == 1
        assert result.categories == 1
        account_service_mock.persist.assert_awaited_once()
        allocation_service_mock.persist.assert_awaited_once()
        category_service_mock.persist.assert_awaited_once()
        expense_service_mock.persist.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_persist_with_allocations_with_categories_with_expenses_children_in_account(
        finance_repository_mock,
        account_service_mock,
        income_service_mock,
        allocation_service_mock,
        category_service_mock,
        expense_service_mock,
        allocation_contribution_service_mock,
        finance,
        account,
        allocation,
        category,
        expense,
        payload_months,
    ):

        reference_year = utcnow().year
        reference_day = 10
        account_bank = account
        account_bank.type = AccountTypeEnum.BANK
        account_bank.name = "Test Account Bank"
        account_bank.initial_balance = 1000

        allocation.account_id = account_bank.id

        category.finance_id = finance.id

        expense.allocation_id = allocation.id
        expense.category_id = category.id
        
        child_category = category
        child_category.id = uuid4()
        child_category.name = "Child Category"
        
        child_expense = expense
        child_expense.id = uuid4()
        child_expense.payee = "Child Expense"
        child_expense.category_id = child_category.id

        payload_children_expenses: list[PayloadPersistChildrenExpenseSchema] = [
            PayloadPersistChildrenExpenseSchema(
                name=child_expense.payee,
                months=payload_months,
                description=child_expense.description
            )
        ]

        payload_children_categories: list[PayloadPersistChildrenCategorySchema] = [
            PayloadPersistChildrenCategorySchema(
                name=child_category.name,
                months=payload_months,
                expenses=payload_children_expenses,
                description=child_category.description,
            )
        ]
        
        payload_parent_expenses: list[PayloadPersistParentExpenseSchema] = [
            PayloadPersistParentExpenseSchema(
                name=expense.payee,
                months=payload_months,
                categories=payload_children_categories,
                description=expense.description,
            )
        ]

        payload_categories: list[PayloadPersistCategorySchema] = [
            PayloadPersistCategorySchema(
                name=category.name,
                expenses=payload_parent_expenses,
                description=category.description,
            )
        ]
        payload_allocations: list[PayloadPersistAllocationSchema] = [
            PayloadPersistAllocationSchema(
                name=allocation.name,
                categories=payload_categories,
                description=allocation.description,
            )
        ]

        payloads: list[PayloadPersistSchema] = [
            PayloadPersistSchema(
                name=account_bank.name,
                type=AccountTypeEnum.BANK,
                incomes=[],
                allocations=payload_allocations,
                reference_day=reference_day,
                reference_year=reference_year,
                initial_balance=account_bank.initial_balance,
            ),
        ]
        service = FinanceService(
            repository=finance_repository_mock,
            account_service=account_service_mock,
            income_service=income_service_mock,
            allocation_service=allocation_service_mock,
            category_service=category_service_mock,
            expense_service=expense_service_mock,
            allocation_contribution_service=allocation_contribution_service_mock,
        )
        account_service_mock.persist.return_value = account_bank
        allocation_service_mock.persist.return_value = allocation
        category_service_mock.persist.side_effect = [category, child_category]
        expense_service_mock.persist.side_effect = [expense, child_expense]
        service.account_service.persist = AsyncMock(return_value=account_bank)
        result = await service.persist(finance=finance, payloads=payloads)
        assert result.accounts == 1
        assert result.incomes == 0
        assert result.allocations == 1
        assert result.expenses == 2
        assert result.categories == 2
        account_service_mock.persist.assert_awaited_once()
        allocation_service_mock.persist.assert_awaited_once()
        category_service_mock.persist.assert_awaited()
        expense_service_mock.persist.assert_awaited()
