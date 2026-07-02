import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.finance.expense_month.repository import ExpenseMonthRepository
from app.domain.finance.expense_month.service import ExpenseMonthService
from app.domain.finance.expense_month.schema import PayloadExpenseMonthPersistSchema
from app.models import ExpenseMonth, Expense, MonthStatusEnum


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
    async def test_persist_list_fills_missing_months(self, expense_month_service, expense):
        payload = [
            PayloadExpenseMonthPersistSchema(
                reference_month=1,
                amount=Decimal("100.00"),
                paid_at=None,
                status=MonthStatusEnum.PENDING,
            ),
            PayloadExpenseMonthPersistSchema(
                reference_month=6,
                amount=Decimal("150.00"),
                paid_at=None,
                status=MonthStatusEnum.PENDING,
            ),
        ]

        with patch.object(
            expense_month_service, "persist", new_callable=AsyncMock
        ) as mock_persist:
            mock_persist.return_value = MagicMock(spec=ExpenseMonth)
            result = await expense_month_service.persist_list(
                expense=expense, reference_year=2026, payload=payload
            )

            # Should have 12 months (original 2 + 10 missing)
            assert len(result) == 12
            assert mock_persist.call_count == 12

    @pytest.mark.asyncio
    async def test_persist_list_all_months_provided(self, expense_month_service, expense):
        payload = [
            PayloadExpenseMonthPersistSchema(
                reference_month=i,
                amount=Decimal("100.00"),
                paid_at=None,
                status=MonthStatusEnum.PENDING,
            )
            for i in range(1, 13)
        ]

        with patch.object(
            expense_month_service, "persist", new_callable=AsyncMock
        ) as mock_persist:
            mock_persist.return_value = MagicMock(spec=ExpenseMonth)
            result = await expense_month_service.persist_list(
                expense=expense, reference_year=2026, payload=payload
            )

            assert len(result) == 12
            assert mock_persist.call_count == 12


class TestExpenseMonthServicePersist:
    @pytest.mark.asyncio
    async def test_persist_new_expense_month(self, expense_month_service, expense):
        payload = PayloadExpenseMonthPersistSchema(
            reference_month=1,
            amount=Decimal("100.00"),
            paid_at=None,
            status=MonthStatusEnum.PENDING,
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
                    expense=expense,
                    payload=payload,
                    reference_year=2026,
                )

                assert result.id == "test-month-id"
                mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_persist_existing_with_throw(self, expense_month_service, expense):
        payload = PayloadExpenseMonthPersistSchema(
            reference_month=1,
            amount=Decimal("100.00"),
            paid_at=None,
            status=MonthStatusEnum.PENDING,
        )

        existing_month = MagicMock(spec=ExpenseMonth)

        with patch.object(
            expense_month_service, "find_by", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = existing_month
            with pytest.raises(HTTPException) as exc_info:
                await expense_month_service.persist(
                    expense=expense,
                    payload=payload,
                    reference_year=2026,
                    with_throw=True,
                )

            assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_persist_existing_without_throw_updates(self, expense_month_service, expense):
        payload = PayloadExpenseMonthPersistSchema(
            reference_month=1,
            amount=Decimal("100.00"),
            paid_at=None,
            status=MonthStatusEnum.PENDING,
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
                    expense=expense,
                    payload=payload,
                    reference_year=2026,
                    with_throw=False,
                )

                assert result.id == "test-month-id"

    @pytest.mark.asyncio
    async def test_persist_with_reference_year_fallback(self, expense_month_service, expense):
        payload = PayloadExpenseMonthPersistSchema(
            reference_month=1,
            amount=Decimal("100.00"),
            paid_at=None,
            status=MonthStatusEnum.PENDING,
            reference_year=None,
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
                await expense_month_service.persist(
                    expense=expense,
                    payload=payload,
                    reference_year=2026,
                )

                # Verify find_by was called with the fallback reference_year
                mock_find.assert_called_once()
                call_kwargs = mock_find.call_args[1]
                assert call_kwargs["reference_year"] == 2026
