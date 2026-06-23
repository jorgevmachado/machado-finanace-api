from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.domain.finance.allocation_contribution.schema import (
    PayloadAllocationContributionCreateListItemSchema,
    PayloadAllocationContributionCreateListSchema,
    PayloadAllocationContributionCreateSchema,
)
from app.domain.finance.allocation_contribution.service import (
    AllocationContributionService,
)
from app.models import utcnow


@pytest.fixture
def allocation_contribution_repository_mock() -> AsyncMock:
    return AsyncMock()


def _finance() -> SimpleNamespace:
    return SimpleNamespace(id=uuid4())


def _payload(
    *,
    reference_year: int | None = None,
    reference_month: int = 1,
    account_id=None,
    allocation_id=None,
    contributor_name: str = "Contributor Name",
) -> PayloadAllocationContributionCreateSchema:
    return PayloadAllocationContributionCreateSchema(
        contributor_name=contributor_name,
        amount=100.0,
        account_id=account_id or uuid4(),
        allocation_id=allocation_id or uuid4(),
        description="Some Description",
        reference_year=reference_year or utcnow().year,
        reference_month=reference_month,
    )


class TestFinanceAllocationContributionServiceFromSession:
    @staticmethod
    @pytest.mark.asyncio
    async def test_from_session_builds_service() -> None:
        service = AllocationContributionService.from_session(AsyncMock())
        assert isinstance(service, AllocationContributionService)


class TestFinanceAllocationContributionCreateService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_create_invalid_year(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        current_year = utcnow().year
        payload = _payload(reference_year=current_year + 1)
        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=_finance(), payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Reference year {current_year + 1} must be less than or equal to the current year {current_year}"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_invalid_month_less_than_1(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        payload = _payload(reference_month=0)
        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=_finance(), payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "Reference month 0 must be between 1 and 12"

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_invalid_month_bigger_than_12(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        payload = _payload(reference_month=13)
        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=_finance(), payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "Reference month 13 must be between 1 and 12"

    @staticmethod
    @pytest.mark.asyncio
    async def test_validate_relations_account_not_found(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )
        finance = _finance()
        account_id = uuid4()
        allocation_id = uuid4()
        service.account_service.find_by = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await service._validate_relations(
                finance=finance, account_id=account_id, allocation_id=allocation_id
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == f"Account with this id {account_id} does not exist"

    @staticmethod
    @pytest.mark.asyncio
    async def test_validate_relations_allocation_not_found(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )
        finance = _finance()
        account_id = uuid4()
        allocation_id = uuid4()
        service.account_service.find_by = AsyncMock(return_value=SimpleNamespace(id=account_id))
        service.allocation_service.find_by = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await service._validate_relations(
                finance=finance, account_id=account_id, allocation_id=allocation_id
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Allocation with this id {allocation_id} does not exist"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_validate_relations_returns_account_and_allocation(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )
        finance = _finance()
        account = SimpleNamespace(id=uuid4())
        allocation = SimpleNamespace(id=uuid4())
        service.account_service.find_by = AsyncMock(return_value=account)
        service.allocation_service.find_by = AsyncMock(return_value=allocation)

        result = await service._validate_relations(
            finance=finance, account_id=account.id, allocation_id=allocation.id
        )

        assert result == (account, allocation)

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_raises_when_contribution_exists(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )
        payload = _payload()
        finance = _finance()
        account = SimpleNamespace(id=payload.account_id)
        allocation = SimpleNamespace(id=payload.allocation_id)
        service.find_by = AsyncMock(return_value=SimpleNamespace(id=uuid4()))

        with pytest.raises(HTTPException) as exc_info:
            await service._persist(
                payload=payload,
                account=account,
                finance=finance,
                allocation=allocation,
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Allocation Contribution with this year {payload.reference_year}, month {payload.reference_month} and name {payload.contributor_name} already exists"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_updates_existing_when_with_throw_false(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )
        payload = _payload()
        finance = _finance()
        account = SimpleNamespace(id=payload.account_id)
        allocation = SimpleNamespace(id=payload.allocation_id)
        existing = SimpleNamespace(id=uuid4(), amount=10.0)
        updated = SimpleNamespace(id=existing.id, amount=payload.amount)
        service.find_by = AsyncMock(return_value=existing)
        service.repository.update.return_value = updated

        result = await service._persist(
            payload=payload,
            account=account,
            finance=finance,
            allocation=allocation,
            with_throw=False,
        )

        assert result is updated
        assert existing.amount == payload.amount
        service.repository.update.assert_awaited_once_with(entity=existing)

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_saves_when_contribution_does_not_exist(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )
        payload = _payload()
        finance = _finance()
        account = SimpleNamespace(id=payload.account_id)
        allocation = SimpleNamespace(id=payload.allocation_id)
        expected = SimpleNamespace(id=uuid4())
        service.find_by = AsyncMock(return_value=None)
        service.repository.save.return_value = expected

        result = await service._persist(
            payload=payload,
            account=account,
            finance=finance,
            allocation=allocation,
        )

        assert result is expected
        service.repository.save.assert_awaited_once()
        saved_entity = service.repository.save.await_args.kwargs["entity"]
        assert saved_entity.amount == payload.amount
        assert saved_entity.finance_id == finance.id
        assert saved_entity.account_id == account.id
        assert saved_entity.allocation_id == allocation.id
        assert saved_entity.description == payload.description
        assert saved_entity.reference_year == payload.reference_year
        assert saved_entity.reference_month == payload.reference_month
        assert saved_entity.contributor_name == payload.contributor_name

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_successfully_calls_validate_and_persist(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )
        payload = _payload()
        finance = _finance()
        account = SimpleNamespace(id=payload.account_id)
        allocation = SimpleNamespace(id=payload.allocation_id)
        expected = SimpleNamespace(id=uuid4())
        service._validate_relations = AsyncMock(return_value=(account, allocation))
        service._persist = AsyncMock(return_value=expected)

        result = await service.create(finance=finance, payload=payload)

        assert result is expected
        service._validate_relations.assert_awaited_once_with(
            finance=finance,
            account_id=payload.account_id,
            allocation_id=payload.allocation_id,
        )
        service._persist.assert_awaited_once_with(
            payload=payload, account=account, finance=finance, allocation=allocation
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_list_by_year_raises_when_empty(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )
        payload = PayloadAllocationContributionCreateListSchema(
            account_id=uuid4(),
            allocation_id=uuid4(),
            description="Some Description",
            contributions=[],
            reference_year=utcnow().year,
        )
        service._validate_relations = AsyncMock(
            return_value=(SimpleNamespace(id=payload.account_id), SimpleNamespace(id=payload.allocation_id))
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_list_by_year(finance=_finance(), payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "Allocation Contribution list cannot be empty"

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_list_by_year_persists_each_item(
        allocation_contribution_repository_mock: AsyncMock,
    ):
        service = AllocationContributionService(
            repository=allocation_contribution_repository_mock
        )
        account_id = uuid4()
        allocation_id = uuid4()
        payload = PayloadAllocationContributionCreateListSchema(
            account_id=account_id,
            allocation_id=allocation_id,
            description="Descricao base",
            contributions=[
                PayloadAllocationContributionCreateListItemSchema(
                    amount=10.0,
                    description="Janeiro",
                    reference_month=1,
                    contributor_name="Fonte A",
                ),
                PayloadAllocationContributionCreateListItemSchema(
                    amount=20.0,
                    description="Fevereiro",
                    reference_month=2,
                    contributor_name="Fonte B",
                ),
            ],
            reference_year=utcnow().year,
        )
        account = SimpleNamespace(id=account_id)
        allocation = SimpleNamespace(id=allocation_id)
        expected = [SimpleNamespace(id=uuid4()), SimpleNamespace(id=uuid4())]
        service._validate_relations = AsyncMock(return_value=(account, allocation))
        service._persist = AsyncMock(side_effect=expected)

        result = await service.create_list_by_year(finance=_finance(), payload=payload)

        assert result == expected
        assert service._persist.await_count == 2
        first_call = service._persist.await_args_list[0].kwargs
        second_call = service._persist.await_args_list[1].kwargs
        assert first_call["with_throw"] is False
        assert second_call["with_throw"] is False
        assert first_call["payload"].reference_year == payload.reference_year
        assert first_call["payload"].reference_month == 1
        assert second_call["payload"].reference_month == 2
