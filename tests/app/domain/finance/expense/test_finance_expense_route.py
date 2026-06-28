from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.domain.finance.expense.route import (
    create,
    expense_service,
    expense_filter,
    list_all,
    find_one,
    update,
    delete,
)
from app.domain.finance.expense.schema import (
    PayloadExpenseCreateSchema,
    PayloadExpenseUpdateSchema,
)
from app.domain.finance.expense.service import (
    ExpenseService,
)
from app.models import utcnow, ExpenseStatusEnum
from app.shared.schemas import FilterPage


def test_expense_builds_service() -> None:
    service = expense_service(AsyncMock())
    assert isinstance(service, ExpenseService)


def test_get_expense_filter_builds_dynamic_filter():
    account_id = uuid4()
    allocation_id = uuid4()
    category_id = uuid4()
    page_filter = expense_filter(
        page=1,
        limit=12,
        status="PAID",
        account_id=str(account_id),
        category_id=str(category_id),
        clean_cache=True,
        with_deleted=False,
        allocation_id=str(allocation_id),
    )

    assert page_filter.page == 1
    assert page_filter.limit == 12
    assert page_filter.status == "PAID"
    assert page_filter.account_id == str(account_id)
    assert page_filter.clean_cache
    assert not page_filter.with_deleted
    assert page_filter.allocation_id == str(allocation_id)
    assert page_filter.category_id == str(category_id)


@pytest.mark.asyncio
async def test_finance_expense_route_create() -> None:
    service = AsyncMock()
    current_date = utcnow()
    payload = PayloadExpenseCreateSchema(
        amount=150.0,
        status=ExpenseStatusEnum.PAID,
        account_id=uuid4(),
        allocation_id=uuid4(),
        category_id=uuid4(),
        description="Some Description",
        paid_at=current_date,
    )
    expected = SimpleNamespace(
        id=uuid4(),
        amount=payload.amount,
        status=payload.status,
        account_id=payload.account_id,
        allocation_id=payload.allocation_id,
        category_id=payload.category_id,
        description=payload.description,
        paid_at=payload.paid_at,
    )
    service.create.return_value = expected
    current_user = SimpleNamespace(id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id"))

    result = await create(service=service, current_user=current_user, payload=payload)

    assert result is expected
    service.create.assert_awaited_once_with(finance=current_user.finance, payload=payload)


@pytest.mark.asyncio
async def test_finance_expense_route_list_all_paginate_and_filter() -> None:
    service = AsyncMock()
    page_filter = expense_filter(page=1, limit=12)
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
    current_date = utcnow()
    expected = SimpleNamespace(
        id=uuid4(),
        amount=150.0,
        status=ExpenseStatusEnum.PAID,
        account_id=uuid4(),
        allocation_id=uuid4(),
        category_id=uuid4(),
        description="Some Description",
        paid_at=current_date,
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
async def test_finance_expense_route_update() -> None:
    service = AsyncMock()
    current_date = utcnow()
    expected = SimpleNamespace(
        id=uuid4(),
        amount=150.0,
        status=ExpenseStatusEnum.PAID,
        account_id=uuid4(),
        allocation_id=uuid4(),
        category_id=uuid4(),
        description="Some Description",
        paid_at=current_date,
    )
    service.update.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )
    payload = PayloadExpenseUpdateSchema(description="Some Description")
    result = await update(
        param="expense-id",
        current_user=current_user,
        service=service,
        payload=payload,
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