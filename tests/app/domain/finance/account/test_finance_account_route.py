from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domain.finance.account.route import (
    create,
    create_list,
    account_service,
    account_filter,
    list_all,
    find_one,
    update,
    delete,
)
from app.domain.finance.account.schema import (
    PayloadAccountCreateSchema,
    PayloadAccountUpdateSchema,
)
from app.domain.finance.account.service import AccountService
from app.models import AccountTypeEnum
from app.shared.schemas import FilterPage


def test_account_builds_service() -> None:
    service = account_service(AsyncMock())
    assert isinstance(service, AccountService)


def test_get_account_filter_builds_dynamic_filter():
    page_filter = account_filter(
        page=1,
        name="nubank",
        type=AccountTypeEnum.BANK,
        limit=12,
        is_active=True,
        clean_cache=True,
    )

    assert page_filter.page == 1
    assert page_filter.name == "nubank"
    assert page_filter.type == "BANK"
    assert page_filter.limit == 12
    assert page_filter.is_active
    assert page_filter.clean_cache


@pytest.mark.asyncio
async def test_finance_account_route_create() -> None:
    service = AsyncMock()
    payload = PayloadAccountCreateSchema(
        name="Test Account", type=AccountTypeEnum.BANK, initial_balance=100.0
    )
    expected = SimpleNamespace(
        id="account-id",
        name=payload.name,
        type=payload.type,
        is_active=True,
        initial_balance=payload.initial_balance,
        current_balance=payload.initial_balance,
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
async def test_finance_account_route_create_list() -> None:
    service = AsyncMock()
    payload = SimpleNamespace(accounts=[])
    expected = [SimpleNamespace(id="account-id")]
    service.create_list.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await create_list(service=service, current_user=current_user, payload=payload)

    assert result == expected
    service.create_list.assert_awaited_once_with(
        finance=current_user.finance, payload=payload
    )


@pytest.mark.asyncio
async def test_finance_account_route_list_all_paginate_and_filter() -> None:
    service = AsyncMock()
    page_filter = account_filter(page=1, limit=12)
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
async def test_finance_account_route_find_one() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(
        id="account-id",
        name="Test Account",
        type=AccountTypeEnum.BANK,
        is_active=True,
        initial_balance=100.00,
        current_balance=100.00,
    )
    service.find_one_cached.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await find_one(
        param="account-id",
        current_user=current_user,
        service=service,
    )

    assert result is expected
    service.find_one_cached.assert_awaited_once_with(
        param="account-id",
        user_request="Finance User",
        clean_cache=False,
        with_deleted=False,
        finance_id="finance-id",
    )


@pytest.mark.asyncio
async def test_finance_account_route_update() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(
        id="account-id",
        name="Test Account",
        type=AccountTypeEnum.BANK,
        is_active=True,
        initial_balance=100.00,
        current_balance=100.00,
    )
    service.update.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )
    payload = PayloadAccountUpdateSchema(name="Test Account")
    result = await update(
        param="account-id", current_user=current_user, service=service, payload=payload
    )

    assert result is expected
    service.update.assert_awaited_once_with(
        param="account-id",
        user_request="Finance User",
        update_schema=payload,
    )


@pytest.mark.asyncio
async def test_finance_account_route_delete() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(message="Deleted Account successfully")
    service.soft_delete.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await delete(
        param="account-id", current_user=current_user, service=service
    )

    assert result is expected
    service.soft_delete.assert_awaited_once_with(
        param="account-id",
        user_request="Finance User",
        finance_id="finance-id",
    )
