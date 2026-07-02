from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.domain.finance.transfer.route import (
    create,
    transfer_service,
    transfer_filter,
    list_all,
    find_one,
    update,
    delete,
)
from app.domain.finance.transfer.schema import (
    PayloadTransferCreateSchema,
    PayloadTransferUpdateSchema,
)
from app.domain.finance.transfer.service import (
    TransferService,
)
from app.models import utcnow
from app.shared.schemas import FilterPage


def test_transfer_builds_service() -> None:
    service = transfer_service(AsyncMock())
    assert isinstance(service, TransferService)


def test_get_transfer_filter_builds_dynamic_filter():
    to_account_id = uuid4()
    from_account_id = uuid4()
    current_date = utcnow()
    transfer_date = date(current_date.year, current_date.month, 1)
    page_filter = transfer_filter(
        page=1,
        limit=12,
        transfer_date=transfer_date,
        to_account_id=str(to_account_id),
        from_account_id=str(from_account_id),
        clean_cache=True,
        with_deleted=False,
    )

    assert page_filter.page == 1
    assert page_filter.limit == 12
    assert page_filter.transfer_date == transfer_date
    assert page_filter.to_account_id == str(to_account_id)
    assert page_filter.from_account_id == str(from_account_id)
    assert page_filter.clean_cache
    assert not page_filter.with_deleted


@pytest.mark.asyncio
async def test_finance_transfer_route_create() -> None:
    service = AsyncMock()
    current_date = utcnow()
    payload = PayloadTransferCreateSchema(
        amount=150.0,
        to_account_id=uuid4(),
        transfer_date=date(current_date.year, current_date.month, 1),
        from_account_id=uuid4(),
        description="Some Description",
    )
    expected = SimpleNamespace(
        id=uuid4(),
        amount=payload.amount,
        description=payload.description,
        transfer_date=payload.transfer_date,
        to_account_id=payload.to_account_id,
        from_account_id=payload.from_account_id,
    )
    service.create.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await create(service=service, current_user=current_user, payload=payload)

    assert result is expected
    service.create.assert_awaited_once_with(
        finance=current_user.finance, payload=payload
    )


@pytest.mark.asyncio
async def test_finance_transfer_route_list_all_paginate_and_filter() -> None:
    service = AsyncMock()
    page_filter = transfer_filter(page=1, limit=12)
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
async def test_finance_transfer_route_find_one() -> None:
    service = AsyncMock()
    current_date = utcnow()
    expected = SimpleNamespace(
        id=uuid4(),
        amount=150.0,
        to_account_id=uuid4(),
        transfer_date=date(current_date.year, current_date.month, 1),
        from_account_id=uuid4(),
        description="Some Description",
    )
    service.find_one_cached.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await find_one(
        param="transfer-id",
        current_user=current_user,
        service=service,
    )

    assert result is expected
    service.find_one_cached.assert_awaited_once_with(
        param="transfer-id",
        user_request="Finance User",
        clean_cache=False,
        with_deleted=False,
        finance_id="finance-id",
    )


@pytest.mark.asyncio
async def test_finance_transfer_route_update() -> None:
    service = AsyncMock()
    current_date = utcnow()
    expected = SimpleNamespace(
        id=uuid4(),
        amount=150.0,
        to_account_id=uuid4(),
        transfer_date=date(current_date.year, current_date.month, 1),
        from_account_id=uuid4(),
        description="Some Description",
    )
    service.update.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )
    payload = PayloadTransferUpdateSchema(description="Some Description")
    result = await update(
        param="transfer-id",
        current_user=current_user,
        service=service,
        payload=payload,
    )

    assert result is expected
    service.update.assert_awaited_once_with(
        param="transfer-id",
        user_request="Finance User",
        update_schema=payload,
    )


@pytest.mark.asyncio
async def test_finance_transfer_route_delete() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(message="Deleted Transfer successfully")
    service.soft_delete.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await delete(
        param="transfer-id", current_user=current_user, service=service
    )

    assert result is expected
    service.soft_delete.assert_awaited_once_with(
        param="transfer-id",
        user_request="Finance User",
        finance_id="finance-id",
    )
