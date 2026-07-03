import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.finance.expense_month.repository import ExpenseMonthRepository
from app.domain.finance.expense_month.service import ExpenseMonthService
from app.domain.finance.months.schema import PayloadMonthPersistSchema
from app.models import ExpenseMonth, Expense, MonthStatusEnum, utcnow


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def expense_month_service(mock_session):
    repository = ExpenseMonthRepository(mock_session)
    return ExpenseMonthService(repository)


@pytest.fixture
def expense():
    expense = MagicMock(spec=Expense)
    expense.id = "test-expense-id"
    expense.finance_id = "test-finance-id"
    return expense


class TestExpenseMonthServicePersistList:
    @pytest.mark.asyncio
    async def test_persist_list_fills_missing_months(
        self, expense_month_service, expense
    ):
        current_datetime = utcnow()
        months = [
            PayloadMonthPersistSchema(
                amount=100.00,
                status=MonthStatusEnum.PENDING,
                reference_month=1,
            ),
            PayloadMonthPersistSchema(
                amount=150.00,
                status=MonthStatusEnum.PENDING,
                reference_month=6,
            ),
        ]

        with patch.object(
            expense_month_service, "persist", new_callable=AsyncMock
        ) as mock_persist:
            mock_persist.return_value = MagicMock(spec=ExpenseMonth)
            result = await expense_month_service.persist_list(
                months=months,
                expense=expense,
                reference_day=current_datetime.day,
                reference_year=current_datetime.year,
            )

            # Should have 12 months (original 2 + 10 missing)
            assert len(result) == 12
            assert mock_persist.call_count == 12

    @pytest.mark.asyncio
    async def test_persist_list_all_months_provided(
        self, expense_month_service, expense
    ):
        current_datetime = utcnow()
        months = [
            PayloadMonthPersistSchema(
                amount=100.00,
                status=MonthStatusEnum.PENDING,
                reference_month=i,
            )
            for i in range(1, 13)
        ]

        with patch.object(
            expense_month_service, "persist", new_callable=AsyncMock
        ) as mock_persist:
            mock_persist.return_value = MagicMock(spec=ExpenseMonth)
            result = await expense_month_service.persist_list(
                months=months,
                expense=expense,
                reference_day=current_datetime.day,
                reference_year=current_datetime.year,
            )

            assert len(result) == 12
            assert mock_persist.call_count == 12


class TestExpenseMonthServicePersist:
    @pytest.mark.asyncio
    async def test_expense_month_persist_new_expense_month(
        self, expense_month_service, expense
    ):
        current_datetime = utcnow()
        month = PayloadMonthPersistSchema(
            status=MonthStatusEnum.PENDING,
            amount=100.00,
            reference_month=1,
        )

        expense_month = MagicMock(spec=ExpenseMonth)
        expense_month.id = "test-month-id"

        with patch.object(
            expense_month_service, "find_by", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = None
            with patch.object(
                expense_month_service.repository, "save", new_callable=AsyncMock
            ) as mock_save:
                mock_save.return_value = expense_month
                result = await expense_month_service.persist(
                    month=month,
                    expense=expense,
                    reference_year=current_datetime.year,
                )

                assert result.id == "test-month-id"
                mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_persist_existing_with_throw(self, expense_month_service, expense):
        current_datetime = utcnow()
        month = PayloadMonthPersistSchema(
            status=MonthStatusEnum.PENDING,
            amount=100.00,
            reference_month=1,
        )

        existing_month = MagicMock(spec=ExpenseMonth)

        with patch.object(
            expense_month_service, "find_by", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = existing_month
            with pytest.raises(HTTPException) as exc_info:
                await expense_month_service.persist(
                    expense=expense,
                    month=month,
                    with_throw=True,
                    reference_year=current_datetime.year,
                )

            assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_persist_existing_without_throw_updates(
        self, expense_month_service, expense
    ):
        current_datetime = utcnow()
        month = PayloadMonthPersistSchema(
            status=MonthStatusEnum.PENDING,
            amount=100.00,
            reference_month=1,
        )

        existing_month = MagicMock(spec=ExpenseMonth)
        existing_month.id = "test-month-id"

        with patch.object(
            expense_month_service, "find_by", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = existing_month
            with patch.object(
                expense_month_service.repository, "update", new_callable=AsyncMock
            ) as mock_update:
                mock_update.return_value = existing_month
                result = await expense_month_service.persist(
                    month=month,
                    expense=expense,
                    with_throw=False,
                    reference_year=current_datetime.year,
                )

                assert result.id == "test-month-id"
