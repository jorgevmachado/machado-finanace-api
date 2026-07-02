from datetime import date
from http import HTTPStatus

import pytest

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.finance.allocation_contribution.repository import (
    AllocationContributionRepository,
)
from app.domain.finance.allocation_contribution_month.schema import (
    PayloadAllocationContributionMonthPersistSchema,
)
from app.domain.finance.allocation_contribution_month.service import (
    AllocationContributionMonthService,
)
from app.models import AllocationContributionMonth, AllocationContribution


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def allocation_contribution_month_service(mock_session):
    repository = AllocationContributionRepository(mock_session)
    return AllocationContributionMonthService(repository)


@pytest.fixture
def allocation_contribution():
    allocation_contribution = MagicMock(spec=AllocationContribution)
    allocation_contribution.id = "test-allocation-contribution-id"
    allocation_contribution.finance_id = "test-finance-id"
    return allocation_contribution


class TestAllocationContributionMonthServicePersistList:
    @pytest.mark.asyncio
    async def test_allocation_contribution_month_service_persist_list_fills_missing_months(
        self,
        allocation_contribution_month_service,
        allocation_contribution,
    ):
        payload = [
            PayloadAllocationContributionMonthPersistSchema(
                amount=100.00,
                received_at=None,
                reference_month=1,
            ),
            PayloadAllocationContributionMonthPersistSchema(
                amount=150.00,
                received_at=None,
                reference_month=6,
            ),
        ]

        with patch.object(
            allocation_contribution_month_service, "persist", new_callable=AsyncMock
        ) as mock_persist:
            mock_persist.return_value = MagicMock(spec=AllocationContributionMonth)
            result = await allocation_contribution_month_service.persist_list(
                allocation_contribution=allocation_contribution,
                payload=payload,
                reference_day=10,
                reference_year=2026,
            )

            # Should have 12 months (original 2 + 10 missing)
            assert len(result) == 12
            assert mock_persist.call_count == 12

    @pytest.mark.asyncio
    async def test_allocation_contribution_month_service_persist_list_all_months_provided(
        self,
        allocation_contribution_month_service,
        allocation_contribution,
    ):
        payload = [
            PayloadAllocationContributionMonthPersistSchema(
                reference_month=i,
                amount=100.00,
                received_at=date(2026, i, 10),
            )
            for i in range(1, 13)
        ]

        with patch.object(
            allocation_contribution_month_service, "persist", new_callable=AsyncMock
        ) as mock_persist:
            mock_persist.return_value = MagicMock(spec=AllocationContributionMonth)
            result = await allocation_contribution_month_service.persist_list(
                payload=payload,
                reference_day=10,
                reference_year=2026,
                allocation_contribution=allocation_contribution,
            )

            assert len(result) == 12
            assert mock_persist.call_count == 12


class TestAllocationContributionMonthServicePersist:
    @pytest.mark.asyncio
    async def test_allocation_contribution_month_service_persist_already_exists_with_throw(
        self,
        allocation_contribution_month_service,
        allocation_contribution,
    ):

        payload = PayloadAllocationContributionMonthPersistSchema(
            amount=100.00,
            received_at=None,
            reference_month=1,
        )

        existing_allocation_contribution_month = MagicMock(
            spec=AllocationContributionMonth
        )

        with patch.object(
            allocation_contribution_month_service, "find_by", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = existing_allocation_contribution_month
            try:
                await allocation_contribution_month_service.persist(
                    payload=payload,
                    with_throw=True,
                    reference_day=10,
                    reference_year=2026,
                    allocation_contribution=allocation_contribution,
                )
                assert False, "Should raise HTTPException"
            except HTTPException as e:
                assert e.status_code == HTTPStatus.BAD_REQUEST
                assert "already exists" in e.detail

    @pytest.mark.asyncio
    async def test_allocation_contribution_month_service_persist_already_exists_without_throw(
        self,
        allocation_contribution_month_service,
        allocation_contribution,
    ):
        payload = PayloadAllocationContributionMonthPersistSchema(
            reference_month=1,
            amount=150.00,
            received_at=None,
        )

        existing_allocation_contribution_month = MagicMock(
            spec=AllocationContributionMonth
        )
        existing_allocation_contribution_month.id = "allocation-contribution-id"

        with patch.object(
            allocation_contribution_month_service, "find_by", new_callable=AsyncMock
        ) as mock_find:
            with patch.object(
                allocation_contribution_month_service.repository,
                "update",
                new_callable=AsyncMock,
            ) as mock_update:
                mock_find.return_value = existing_allocation_contribution_month
                mock_update.return_value = existing_allocation_contribution_month

                result = await allocation_contribution_month_service.persist(
                    allocation_contribution=allocation_contribution,
                    payload=payload,
                    reference_year=2026,
                    reference_day=10,
                    with_throw=False,
                )

                assert result == existing_allocation_contribution_month
                mock_update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_allocation_contribution_month_service_persist_create_new(
        self,
        allocation_contribution_month_service,
        allocation_contribution,
    ):
        payload = PayloadAllocationContributionMonthPersistSchema(
            amount=150.00,
            received_at=date(2026, 1, 10),
            reference_month=1,
        )

        created_allocation_contribution_month = MagicMock(
            spec=AllocationContributionMonth
        )
        created_allocation_contribution_month.id = "allocation-contribution-id"

        with patch.object(
            allocation_contribution_month_service, "find_by", new_callable=AsyncMock
        ) as mock_find:
            with patch.object(
                allocation_contribution_month_service.repository,
                "save",
                new_callable=AsyncMock,
            ) as mock_save:
                mock_find.return_value = None
                mock_save.return_value = created_allocation_contribution_month

                result = await allocation_contribution_month_service.persist(
                    allocation_contribution=allocation_contribution,
                    payload=payload,
                    reference_year=2026,
                    reference_day=10,
                    with_throw=False,
                )

                assert result == created_allocation_contribution_month
                mock_save.assert_awaited_once()
