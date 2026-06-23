from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import date

import pytest

from app.domain.finance.income.route import (
    create,
    income_service,
    income_filter,
    list_all,
    find_one,
    update,
    delete,
    create_list_by_year,
)
from app.domain.finance.income.schema import (
    PayloadIncomeCreateSchema,
    PayloadIncomeUpdateSchema,
    PayloadIncomeCreateListItemSchema,
    PayloadIncomeCreateListSchema,
)
from app.domain.finance.income.service import IncomeService
from app.shared.schemas import FilterPage


def test_income_builds_service() -> None:
    service = income_service(AsyncMock())
    assert isinstance(service, IncomeService)


def test_get_income_filter_builds_dynamic_filter():
    finance_id = uuid4()
    account_id = uuid4()
    page_filter = income_filter(
        page=1,
        source="Source Name",
        limit=12,
        finance_id=str(finance_id),
        account_id=str(account_id),
        source_code="source_name",
        clean_cache=True,
        with_deleted=False,
        reference_year=2026,
        reference_month=1,
    )

    assert page_filter.page == 1
    assert page_filter.source == "Source Name"
    assert page_filter.limit == 12
    assert page_filter.finance_id == str(finance_id)
    assert page_filter.account_id == str(account_id)
    assert page_filter.source_code == "source_name"
    assert page_filter.clean_cache
    assert not page_filter.with_deleted
    assert page_filter.reference_year == 2026
    assert page_filter.reference_month == 1


@pytest.mark.asyncio
async def test_finance_income_route_create() -> None:
    service = AsyncMock()
    account_id = uuid4()
    payload = PayloadIncomeCreateSchema(
        source="Source Name",
        amount=100.00,
        account_id=account_id,
        description="Some Description",
        reference_year=2026,
        reference_month=1,
        received_at=date(2026, 1, 1),
    )
    expected = SimpleNamespace(
        id="income-id",
        source="Source Name",
        amount=100.00,
        account_id=account_id,
        source_name="source_name",
        description="Some Description",
        reference_year=2026,
        reference_month=1,
        received_at=date(2026, 1, 1),
    )
    service.create.return_value = expected
    current_user = SimpleNamespace(id="user-id", username="Finance User")

    result = await create(service=service, current_user=current_user, payload=payload)

    assert result is expected
    service.create.assert_awaited_once_with(current_user=current_user, payload=payload)


@pytest.mark.asyncio
async def test_finance_income_route_list_all_paginate_and_filter() -> None:
    service = AsyncMock()
    page_filter = income_filter(page=1, limit=12)
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
async def test_finance_income_route_find_one() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(
        id="income-id",
        source="Source Name",
        amount=100.00,
        source_name="source_name",
        description="Some Description",
        reference_year=2026,
        reference_month=1,
        received_at=date(2026, 1, 1),
    )
    service.find_one_cached.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await find_one(
        param="income-id",
        current_user=current_user,
        service=service,
    )

    assert result is expected
    service.find_one_cached.assert_awaited_once_with(
        param="income-id",
        user_request="Finance User",
        clean_cache=False,
        with_deleted=False,
        finance_id="finance-id",
    )


@pytest.mark.asyncio
async def test_finance_income_route_update() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(
        id="income-id",
        source="Source Name",
        amount=100.00,
        source_name="source_name",
        description="Some Description",
        reference_year=2026,
        reference_month=1,
        received_at=date(2026, 1, 1),
    )
    service.update.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )
    payload = PayloadIncomeUpdateSchema(reference_month=2)
    result = await update(
        param="income-id", current_user=current_user, service=service, payload=payload
    )

    assert result is expected
    service.update.assert_awaited_once_with(
        param="income-id",
        user_request="Finance User",
        update_schema=payload,
    )


@pytest.mark.asyncio
async def test_finance_income_route_delete() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(message="Deleted Income successfully")
    service.soft_delete.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await delete(param="income-id", current_user=current_user, service=service)

    assert result is expected
    service.soft_delete.assert_awaited_once_with(
        param="income-id",
        user_request="Finance User",
        finance_id="finance-id",
    )


@pytest.mark.asyncio
async def test_finance_income_route_create_list() -> None:
    service = AsyncMock()
    account_id = uuid4()
    payload_item = PayloadIncomeCreateListItemSchema(amount=100.00, reference_month=1)
    payload = PayloadIncomeCreateListSchema(
        account_id=uuid4(),
        source="Test Income",
        reference_day=5,
        reference_year=2026,
        description="Some Description",
        incomes=[
            payload_item
        ],
    )
    
    expected = [SimpleNamespace(
        id="income-id",
        source="Source Name",
        amount=100.00,
        account_id=account_id,
        source_name="source_name",
        description="Some Description",
        reference_year=2026,
        reference_month=1,
        received_at=date(2026, 1, 1),
    )]
    
    service.create_list_by_year.return_value = expected
    current_user = SimpleNamespace(id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id"))

    result = await create_list_by_year(service=service, current_user=current_user, payload=payload)

    assert result is expected
    service.create_list_by_year.assert_awaited_once_with(current_user=current_user, payload=payload)