from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domain.finance.allocation.route import (
    create,
    allocation_service,
    allocation_filter,
    list_all,
    find_one,
    update,
    delete,
)
from app.domain.finance.allocation.schema import (
    PayloadAllocationCreateSchema,
    PayloadAllocationUpdateSchema,
)
from app.domain.finance.allocation.service import AllocationService
from app.models import AllocationTypeEnum
from app.shared.schemas import FilterPage


def test_allocation_builds_service() -> None:
    service = allocation_service(AsyncMock())
    assert isinstance(service, AllocationService)


def test_allocation_builds_dynamic_filter():
    page_filter = allocation_filter(
        page=1,
        name="home",
        type=AllocationTypeEnum.OTHER,
        limit=12,
        is_active=True,
        clean_cache=True,
        with_deleted=False,
    )

    assert page_filter.page == 1
    assert page_filter.name == "home"
    assert page_filter.type == "OTHER"
    assert page_filter.limit == 12
    assert page_filter.is_active
    assert page_filter.clean_cache


@pytest.mark.asyncio
async def test_finance_allocation_route_create() -> None:
    service = AsyncMock()
    payload = PayloadAllocationCreateSchema(
        name="Test Allocation",
        type=AllocationTypeEnum.OTHER,
        description="Some Description",
    )
    expected = SimpleNamespace(
        id="allocation-id",
        name=payload.name,
        name_code="test_allocation",
        type=payload.type,
        is_active=True,
        description=payload.description,
    )
    service.persist.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await create(service=service, current_user=current_user, payload=payload)

    assert result is expected
    service.persist.assert_awaited_once_with(
        finance=current_user.finance, payload=payload
    )

@pytest.mark.asyncio
async def test_finance_allocation_route_list_all_paginate_and_filter() -> None:
    service = AsyncMock()
    page_filter = allocation_filter(page=1, limit=12)
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
async def test_finance_allocation_route_find_one() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(
        id="allocation-id",
        name="Test Allocation",
        type=AllocationTypeEnum.OTHER,
        is_active=True,
        description="Some Description",
    )
    service.find_one_cached.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await find_one(
        param="allocation-id",
        current_user=current_user,
        service=service,
    )

    assert result is expected
    service.find_one_cached.assert_awaited_once_with(
        param="allocation-id",
        user_request="Finance User",
        clean_cache=False,
        with_deleted=False,
        finance_id="finance-id",
    )


@pytest.mark.asyncio
async def test_finance_allocation_route_update() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(
        id="allocation-id",
        name="Test Allocation",
        type=AllocationTypeEnum.OTHER,
        is_active=True,
        description="Some Description",
    )
    service.update.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )
    payload = PayloadAllocationUpdateSchema(name="Test Allocation")
    result = await update(
        param="allocation-id",
        current_user=current_user,
        service=service,
        payload=payload,
    )

    assert result is expected
    service.update.assert_awaited_once_with(
        param="allocation-id",
        user_request="Finance User",
        update_schema=payload,
    )


@pytest.mark.asyncio
async def test_finance_allocation_route_delete() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(message="Deleted Allocation successfully")
    service.soft_delete.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await delete(
        param="allocation-id", current_user=current_user, service=service
    )

    assert result is expected
    service.soft_delete.assert_awaited_once_with(
        param="allocation-id",
        user_request="Finance User",
        finance_id="finance-id",
    )
