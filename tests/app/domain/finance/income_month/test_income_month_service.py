from datetime import date

import pytest

from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.finance.income_month.repository import IncomeMonthRepository
from app.domain.finance.income_month.schema import PayloadIncomeMonthPersistSchema
from app.domain.finance.income_month.service import IncomeMonthService
from app.models import Income, IncomeMonth


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def income_month_service(mock_session):
    repository = IncomeMonthRepository(mock_session)
    return IncomeMonthService(repository)


@pytest.fixture
def income():
    income = MagicMock(spec=Income)
    income.id = "test-income-id"
    income.finance_id = "test-finance-id"
    return income



class TestIncomeMonthServicePersistList:
    @pytest.mark.asyncio
    async def test_income_month_persist_list_fills_missing_months(
        self,
            income_month_service, 
            income
    ):
        payload = [
            PayloadIncomeMonthPersistSchema(
                reference_month=1,
                amount=100.00,
                received_at=None,
            ),
            PayloadIncomeMonthPersistSchema(
                reference_month=6,
                amount=150.00,
                received_at=None,
            ),
        ]

        with patch.object(
            income_month_service, "persist", new_callable=AsyncMock
        ) as mock_persist:
            mock_persist.return_value = MagicMock(spec=IncomeMonth)
            result = await income_month_service.persist_list(
                income=income,
                reference_day=10,
                reference_year=2026,
                payload=payload
            )

            # Should have 12 months (original 2 + 10 missing)
            assert len(result) == 12
            assert mock_persist.call_count == 12

    @pytest.mark.asyncio
    async def test_income_month_persist_list_all_months_provided(
        self,
            income_month_service,
            income
    ):
        payload = [
            PayloadIncomeMonthPersistSchema(
                reference_month=i,
                amount=100.00,
                received_at=date(2026, i, 10),
            )
            for i in range(1, 13)
        ]

        with patch.object(
            income_month_service, "persist", new_callable=AsyncMock
        ) as mock_persist:
            mock_persist.return_value = MagicMock(spec=IncomeMonth)
            result = await income_month_service.persist_list(
                income=income,
                reference_day=10,
                reference_year=2026,
                payload=payload
            )

            assert len(result) == 12
            assert mock_persist.call_count == 12

    @pytest.mark.asyncio
    async def test_income_month_persist_already_exists_with_throw(
        self,
        income_month_service,
        income
    ):
        from http import HTTPStatus
        from fastapi import HTTPException
        
        payload = PayloadIncomeMonthPersistSchema(
            reference_month=1,
            amount=100.00,
            received_at=None,
        )
        
        existing_income_month = MagicMock(spec=IncomeMonth)
        
        with patch.object(
            income_month_service, "find_by", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = existing_income_month
            
            try:
                await income_month_service.persist(
                    income=income,
                    payload=payload,
                    reference_year=2026,
                    reference_day=10,
                    with_throw=True,
                )
                assert False, "Should raise HTTPException"
            except HTTPException as e:
                assert e.status_code == HTTPStatus.BAD_REQUEST
                assert "already exists" in e.detail

    @pytest.mark.asyncio
    async def test_income_month_persist_already_exists_without_throw(
        self,
        income_month_service,
        income
    ):
        payload = PayloadIncomeMonthPersistSchema(
            reference_month=1,
            amount=150.00,
            received_at=None,
        )
        
        existing_income_month = MagicMock(spec=IncomeMonth)
        existing_income_month.id = "income-month-id"
        
        with patch.object(
            income_month_service, "find_by", new_callable=AsyncMock
        ) as mock_find:
            with patch.object(
                income_month_service.repository, "update", new_callable=AsyncMock
            ) as mock_update:
                mock_find.return_value = existing_income_month
                mock_update.return_value = existing_income_month
                
                result = await income_month_service.persist(
                    income=income,
                    payload=payload,
                    reference_year=2026,
                    reference_day=10,
                    with_throw=False,
                )
                
                assert result == existing_income_month
                mock_update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_income_month_persist_creates_new(
        self,
        income_month_service,
        income
    ):
        from datetime import date
        
        payload = PayloadIncomeMonthPersistSchema(
            reference_month=1,
            amount=200.00,
            received_at=date(2026, 1, 10),
        )
        
        created_income_month = MagicMock(spec=IncomeMonth)
        created_income_month.id = "new-income-month-id"
        
        with patch.object(
            income_month_service, "find_by", new_callable=AsyncMock
        ) as mock_find:
            with patch.object(
                income_month_service.repository, "save", new_callable=AsyncMock
            ) as mock_save:
                mock_find.return_value = None
                mock_save.return_value = created_income_month
                
                result = await income_month_service.persist(
                    income=income,
                    payload=payload,
                    reference_year=2026,
                    reference_day=10,
                )
                
                assert result == created_income_month
                mock_save.assert_awaited_once()