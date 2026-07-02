from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domain.finance.expense.route import (
    create,
    list_all,
    find_one,
    update,
    delete,
    expense_service,
)
from app.domain.finance.expense.service import ExpenseService
from app.shared.schemas import FilterPage


def test_expense_builds_service() -> None:
    service = expense_service(AsyncMock())
    assert isinstance(service, ExpenseService)


@pytest.mark.asyncio
async def test_finance_expense_route_list_all() -> None:
    service = AsyncMock()
    page_filter = FilterPage.build(page=1, limit=12)
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
async def test_finance_expense_route_find_one() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(
        id="expense-id",
        description="Test Expense",
    )
    service.find_one_cached.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await find_one(
        param="expense-id",
        current_user=current_user,
        service=service,
    )

    assert result is expected
    service.find_one_cached.assert_awaited_once_with(
        param="expense-id",
        user_request="Finance User",
        clean_cache=False,
        with_deleted=False,
        finance_id="finance-id",
    )


@pytest.mark.asyncio
async def test_finance_expense_route_create() -> None:
    service = AsyncMock()
    payload = SimpleNamespace(
        account_id="account-id",
        category_id="category-id",
        allocation_id="allocation-id",
        description="Test Expense",
        reference_day=1,
        reference_year=2026,
        months=[],
    )
    expected = SimpleNamespace(
        id="expense-id",
        description=payload.description,
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
async def test_finance_expense_route_update() -> None:
    service = AsyncMock()
    payload = SimpleNamespace(description="Updated Expense")
    expected = SimpleNamespace(
        id="expense-id",
        description="Updated Expense",
    )
    service.update.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await update(
        param="expense-id", current_user=current_user, service=service, payload=payload
    )

    assert result is expected
    service.update.assert_awaited_once_with(
        param="expense-id",
        user_request="Finance User",
        update_schema=payload,
    )


@pytest.mark.asyncio
async def test_finance_expense_route_delete() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(message="Deleted Expense successfully")
    service.soft_delete.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await delete(
        param="expense-id", current_user=current_user, service=service
    )

    assert result is expected
    service.soft_delete.assert_awaited_once_with(
        param="expense-id",
        user_request="Finance User",
        finance_id="finance-id",
    )
