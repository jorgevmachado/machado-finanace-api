from datetime import date
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi_pagination import LimitOffsetParams

from app.core.pagination import CustomLimitOffsetPage
from app.domain.finance.account.repository import AccountRepository
from app.models import (
    Account,
    Allocation,
    Expense,
    ExpenseMonth,
    Income,
    IncomeMonth,
    MonthStatusEnum,
    utcnow,
    AccountTypeEnum,
    AllocationContribution,
    AllocationContributionMonth,
)
from app.shared.schemas import FilterPage


@pytest.fixture
def expense():
    expense = MagicMock(spec=Expense)
    expense.id = uuid4()
    expense.months = []
    expense.payee = "Test Payee"
    expense.parent_id = None
    expense.payee_code = "test_payee"
    expense.category_id = uuid4()
    expense.description = "Test Expense Description"
    expense.created_at = utcnow()
    expense.updated_at = None
    expense.deleted_at = None
    expense.allocation_id = uuid4()
    return expense


@pytest.fixture()
def income():
    income = MagicMock(spec=Income)
    income.id = uuid4()
    income.months = []
    income.source = "Test Income"
    income.account_id = uuid4()
    income.source_code = "test_income"
    income.description = "Test Income Description"
    income.created_at = utcnow()
    income.updated_at = None
    income.deleted_at = None
    return income


@pytest.fixture
def allocation():
    allocation = MagicMock(spec=Allocation)
    allocation.id = uuid4()
    allocation.name = "Test Allocation"
    allocation.name_code = "test_allocation"
    allocation.account_id = uuid4()
    allocation.description = "Test Allocation Description"
    allocation.is_active = True
    allocation.expenses = []
    allocation.created_at = utcnow()
    allocation.updated_at = None
    allocation.deleted_at = None
    allocation.allocation_contributions = []
    return allocation

@pytest.fixture
def allocation_contribution():
    allocation_contribution = MagicMock(spec=AllocationContribution)
    allocation_contribution.id = uuid4()
    allocation_contribution.allocation_id = uuid4()
    allocation_contribution.months = []
    allocation_contribution.contributor_name = "Test Contributor"
    allocation_contribution.contributor_name_code = "test_contributor"
    allocation_contribution.description = "Test Allocation Contribution Description"
    allocation_contribution.created_at = utcnow()
    allocation_contribution.updated_at = None
    allocation_contribution.deleted_at = None
    return allocation_contribution
    

@pytest.fixture
def account(income, allocation, expense, allocation_contribution):
    account = MagicMock(spec=Account)

    account.id = uuid4()
    account.type = AccountTypeEnum.BANK
    account.name = "Test Account"
    account.name_code = "test_account"
    account.is_active = True
    account.finance_id = uuid4()
    account.created_at = utcnow()
    account.updated_at = None
    account.deleted_at = None
    account.current_balance = 0
    account.initial_balance = 0

    account.outgoing_transfers = []
    account.incoming_transfers = []

    for i in range(1, 13):
        income_month_2025 = MagicMock(spec=IncomeMonth)
        income_month_2025.id = uuid4()
        income_month_2025.amount = 100
        income_month_2025.income_id = income.id
        income_month_2025.reference_year = 2025
        income_month_2025.reference_month = i
        income_month_2025.received_at = date(year=2025, month=i, day=1)
        income_month_2025.created_at = utcnow()
        income_month_2025.updated_at = None
        income_month_2025.deleted_at = None
        income.months.append(income_month_2025)

        expense_month_2025 = MagicMock(spec=ExpenseMonth)
        expense_month_2025.id = uuid4()
        expense_month_2025.amount = 200
        expense_month_2025.status = MonthStatusEnum.PAID
        expense_month_2025.paid_at = utcnow()
        expense_month_2025.expense_id = expense.id
        expense_month_2025.created_at = utcnow()
        expense_month_2025.updated_at = None
        expense_month_2025.deleted_at = None
        expense_month_2025.reference_year = 2025
        expense_month_2025.reference_month = i
        expense.months.append(expense_month_2025)

        allocation_contribution_month_2025 = MagicMock(spec=AllocationContributionMonth)
        allocation_contribution_month_2025.id = uuid4()
        allocation_contribution_month_2025.amount = 300
        allocation_contribution_month_2025.allocation_contribution_id = allocation_contribution.id
        allocation_contribution_month_2025.reference_year = 2025
        allocation_contribution_month_2025.reference_month = i
        allocation_contribution_month_2025.received_at = date(year=2025, month=i, day=1)
        allocation_contribution_month_2025.created_at = utcnow()
        allocation_contribution_month_2025.updated_at = None
        allocation_contribution_month_2025.deleted_at = None
        allocation_contribution.months.append(allocation_contribution_month_2025)
        

        income_month_2026 = MagicMock(spec=IncomeMonth)
        income_month_2026.id = uuid4()
        income_month_2026.amount = 400
        income_month_2026.income_id = income.id
        income_month_2026.reference_year = 2026
        income_month_2026.reference_month = i
        income_month_2026.received_at = date(year=2026, month=i, day=1)
        income_month_2026.created_at = utcnow()
        income_month_2026.updated_at = None
        income_month_2026.deleted_at = None
        income.months.append(income_month_2026)

        expense_month_2026 = MagicMock(spec=ExpenseMonth)
        expense_month_2026.id = uuid4()
        expense_month_2026.amount = 500
        expense_month_2026.status = MonthStatusEnum.PAID
        expense_month_2026.paid_at = utcnow()
        expense_month_2026.expense_id = expense.id
        expense_month_2026.created_at = utcnow()
        expense_month_2026.updated_at = None
        expense_month_2026.deleted_at = None
        expense_month_2026.reference_year = 2026
        expense_month_2026.reference_month = i
        expense.months.append(expense_month_2026)

        allocation_contribution_month_2026 = MagicMock(spec=AllocationContributionMonth)
        allocation_contribution_month_2026.id = uuid4()
        allocation_contribution_month_2026.amount = 600
        allocation_contribution_month_2026.allocation_contribution_id = allocation_contribution.id    
        allocation_contribution_month_2026.reference_year = 2026
        allocation_contribution_month_2026.reference_month = i
        allocation_contribution_month_2026.received_at = date(year=2026, month=i, day=1)
        allocation_contribution_month_2026.created_at = utcnow()
        allocation_contribution_month_2026.updated_at = None
        allocation_contribution_month_2026.deleted_at = None
        allocation_contribution.months.append(allocation_contribution_month_2026)
    
    expense.allocation_id = allocation.id
    allocation_contribution.allocation_id = allocation.id
    
    account.incomes = [income]
    allocation.expenses = [expense]
    allocation.allocation_contributions = [allocation_contribution]
    account.allocations = [allocation]

    return account


class TestFinanceAccountRepositoryListAll:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_account_repository_list_all_with_reference_year_none(
         account
    ):
        expected_items = [account]
        scalars_result = Mock()
        scalars_result.all.return_value = expected_items

        mock_session = AsyncMock()
        mock_session.scalars = AsyncMock(return_value=scalars_result)

        repository = AccountRepository(session=mock_session)

        with patch("app.core.repository.base.is_paginate", return_value=False):
            result = await repository.list_all()

        assert result[0] == account

        result_incomes = result[0].incomes
        result_income = result_incomes[0]
        assert len(result_income.months) == 24

        result_allocations = result[0].allocations
        result_allocation = result_allocations[0]

        result_expenses = result_allocation.expenses
        result_expense = result_expenses[0]
        assert len(result_expense.months) == 24

        result_allocation_contributions = result_allocation.allocation_contributions
        result_allocation_contribution = result_allocation_contributions[0]
        assert len(result_allocation_contribution.months) == 24

        mock_session.scalars.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_account_repository_list_all_with_reference_year_and_list(
         account
    ):
        expected_items = [account]
        scalars_result = Mock()
        scalars_result.all.return_value = expected_items

        mock_session = AsyncMock()
        mock_session.scalars = AsyncMock(return_value=scalars_result)
        page_filter = FilterPage()

        repository = AccountRepository(session=mock_session)

        with patch("app.core.repository.base.is_paginate", return_value=False):
            result = await repository.list_all(
                page_filter=FilterPage.build(
                    page_filter=page_filter, reference_year=2026
                )
            )

        result_incomes = result[0].incomes
        result_income = result_incomes[0]
        assert len(result_income.months) == 12

        result_allocations = result[0].allocations
        result_allocation = result_allocations[0]

        result_expenses = result_allocation.expenses
        result_expense = result_expenses[0]
        assert len(result_expense.months) == 12

        result_allocation_contributions = result_allocation.allocation_contributions
        result_allocation_contribution = result_allocation_contributions[0]
        assert len(result_allocation_contribution.months) == 12

        mock_session.scalars.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_account_repository_list_all_with_reference_year_and_list_with_allocations_empty(
        account,
    ):
        expected_items = [account]
        scalars_result = Mock()
        scalars_result.all.return_value = expected_items

        mock_session = AsyncMock()
        mock_session.scalars = AsyncMock(return_value=scalars_result)
        page_filter = FilterPage()

        repository = AccountRepository(session=mock_session)

        with patch("app.core.repository.base.is_paginate", return_value=False):
            result = await repository.list_all(
                page_filter=FilterPage.build(
                    page_filter=page_filter, reference_year=2000
                )
            )

        result_account = result[0]
        result_incomes = result_account.incomes
        assert len(result_incomes) == 0

        result_allocations = result_account.allocations
        assert len(result_allocations) == 0

        mock_session.scalars.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_account_repository_list_all_with_reference_year_and_paginate(
         account
    ):
        params = LimitOffsetParams(limit=50, offset=0)
        expected_page = CustomLimitOffsetPage.create(
            items=[account],
            total=1,
            params=params,
        )
        mock_session = AsyncMock()
        repository = AccountRepository(session=mock_session)
        page_filter = FilterPage(offset=0, limit=50)

        with (
            patch("app.core.repository.base.is_paginate", return_value=True),
            patch(
                "app.core.repository.base.get_limit_offset_params",
                return_value=params,
            ),
            patch(
                "app.core.repository.base.paginate", new_callable=AsyncMock
            ) as paginate_mock,
        ):
            paginate_mock.return_value = expected_page
            result = await repository.list_all(
                page_filter=FilterPage.build(
                    page_filter=page_filter, reference_year=2025
                )
            )

        assert result is expected_page
        result_items = result.items
        result_incomes = result_items[0].incomes
        result_income = result_incomes[0]
        assert len(result_income.months) == 12

        result_allocations = result_items[0].allocations
        result_allocation = result_allocations[0]

        result_expenses = result_allocation.expenses
        result_expense = result_expenses[0]
        assert len(result_expense.months) == 12

        result_allocation_contributions = result_allocation.allocation_contributions
        result_allocation_contribution = result_allocation_contributions[0]
        assert len(result_allocation_contribution.months) == 12
