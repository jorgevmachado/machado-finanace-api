from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.domain.finance.allocation_contribution.route import (
    create,
    create_list_by_year,
    allocation_contribution_service,
    allocation_contribution_filter,
    list_all,
    find_one,
    update,
    delete,
)
from app.domain.finance.allocation_contribution.schema import (
    PayloadAllocationContributionCreateSchema,
    PayloadAllocationContributionUpdateSchema,
)
from app.domain.finance.allocation_contribution.service import (
    AllocationContributionService,
)
from app.models import utcnow
from app.shared.schemas import FilterPage


def test_allocation_contribution_builds_service() -> None:
    service = allocation_contribution_service(AsyncMock())
    assert isinstance(service, AllocationContributionService)


def test_get_allocation_contribution_filter_builds_dynamic_filter():
    finance_id = uuid4()
    account_id = uuid4()
    allocation_id = uuid4()
    page_filter = allocation_contribution_filter(
        page=1,
        limit=12,
        finance_id=str(finance_id),
        account_id=str(account_id),
        clean_cache=True,
        with_deleted=False,
        allocation_id=str(allocation_id),
        reference_year=2026,
        reference_month=1,
        contributor_name="Contributor Name",
    )

    assert page_filter.page == 1
    assert page_filter.limit == 12
    assert page_filter.finance_id == str(finance_id)
    assert page_filter.account_id == str(account_id)
    assert page_filter.clean_cache
    assert not page_filter.with_deleted
    assert page_filter.allocation_id == str(allocation_id)
    assert page_filter.reference_year == 2026
    assert page_filter.reference_month == 1
    assert page_filter.contributor_name == "Contributor Name"


@pytest.mark.asyncio
async def test_finance_allocation_contribution_route_create() -> None:
    service = AsyncMock()
    payload = PayloadAllocationContributionCreateSchema(
        contributor_name="Contributor Name",
        amount=100.0,
        account_id=uuid4(),
        allocation_id=uuid4(),
        description="Some Description",
        reference_year=utcnow().year,
        reference_month=1,
    )
    expected = SimpleNamespace(
        id=uuid4(),
        contributor_name=payload.contributor_name,
        amount=payload.amount,
        account_id=payload.account_id,
        allocation_id=payload.allocation_id,
        description=payload.description,
        reference_year=payload.reference_year,
        reference_month=payload.reference_month,
    )
    service.create.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await create(service=service, current_user=current_user, payload=payload)

    assert result is expected
    service.create.assert_awaited_once_with(finance=current_user.finance, payload=payload)


@pytest.mark.asyncio
async def test_finance_allocation_contribution_route_create_list_by_year() -> None:
    service = AsyncMock()
    payload = SimpleNamespace(contributions=[])
    expected = [SimpleNamespace(id=uuid4())]
    service.create_list_by_year.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await create_list_by_year(
        service=service, current_user=current_user, payload=payload
    )

    assert result == expected
    service.create_list_by_year.assert_awaited_once_with(
        finance=current_user.finance, payload=payload
    )


@pytest.mark.asyncio
async def test_finance_allocation_contribution_route_list_all_paginate_and_filter() -> (
    None
):
    service = AsyncMock()
    page_filter = allocation_contribution_filter(page=1, limit=12)
    expected = SimpleNamespace(items=[])
    service.list_all_cached.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await list_all(
        current_user=current_user,
        service=service,
        page_filter=page_filter,
    )

    assert result is expected
    service.list_all_cached.assert_awaited_once()
    called_page_filter = service.list_all_cached.await_args.kwargs["page_filter"]

    assert (
        called_page_filter.model_dump()
        == FilterPage.build(
            page_filter=page_filter, finance_id="finance-id"
        ).model_dump()
    )
    assert service.list_all_cached.await_args.kwargs["user_request"] == "Finance User"


@pytest.mark.asyncio
async def test_finance_allocation_contribution_route_find_one() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(
        id=uuid4(),
        contributor_name="Contributor Name",
        amount=100.0,
        account_id=uuid4(),
        allocation_id=uuid4(),
        description="Some Description",
        reference_year=utcnow().year,
        reference_month=1,
    )
    service.find_one_cached.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await find_one(
        param="allocation-contribuition-id",
        current_user=current_user,
        service=service,
    )

    assert result is expected
    service.find_one_cached.assert_awaited_once_with(
        param="allocation-contribuition-id",
        user_request="Finance User",
        clean_cache=False,
        with_deleted=False,
        finance_id="finance-id",
    )


@pytest.mark.asyncio
async def test_finance_allocation_contribution_route_update() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(
        id=uuid4(),
        contributor_name="Contributor Name",
        amount=100.0,
        account_id=uuid4(),
        allocation_id=uuid4(),
        description="Some Description",
        reference_year=utcnow().year,
        reference_month=1,
    )
    service.update.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )
    payload = PayloadAllocationContributionUpdateSchema(reference_month=2)
    result = await update(
        param="allocation-contribuition-id",
        current_user=current_user,
        service=service,
        payload=payload,
    )

    assert result is expected
    service.update.assert_awaited_once_with(
        param="allocation-contribuition-id",
        user_request="Finance User",
        update_schema=payload,
    )


@pytest.mark.asyncio
async def test_finance_allocation_contribution_route_delete() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(message="Deleted AllocationContribution successfully")
    service.soft_delete.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await delete(
        param="allocation-contribuition-id", current_user=current_user, service=service
    )

    assert result is expected
    service.soft_delete.assert_awaited_once_with(
        param="allocation-contribuition-id",
        user_request="Finance User",
        finance_id="finance-id",
    )
