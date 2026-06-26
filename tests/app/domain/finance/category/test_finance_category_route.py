from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.domain.finance.category.route import (
    create,
    create_list,
    category_service,
    category_filter,
    list_all,
    find_one,
    update,
    delete,
)
from app.domain.finance.category.schema import (
    PayloadCategoryCreateSchema,
    PayloadCategoryUpdateSchema,
)
from app.domain.finance.category.service import CategoryService
from app.models import CategoryTypeEnum
from app.shared.schemas import FilterPage
from app.shared.utils.string import to_snake_case


def test_category_builds_service() -> None:
    service = category_service(AsyncMock())
    assert isinstance(service, CategoryService)


def test_get_category_filter_builds_dynamic_filter():
    page_filter = category_filter(
        page=1,
        name="Category Name",
        type=CategoryTypeEnum.OTHER,
        limit=12,
        clean_cache=True,
    )

    assert page_filter.page == 1
    assert page_filter.name == "Category Name"
    assert page_filter.type == "OTHER"
    assert page_filter.limit == 12
    assert page_filter.clean_cache


@pytest.mark.asyncio
async def test_finance_category_route_create() -> None:
    service = AsyncMock()
    finance_id = uuid4()
    payload = PayloadCategoryCreateSchema(
        name="Test Category",
        type=CategoryTypeEnum.OTHER,
        description="Some Description",
    )
    expected = SimpleNamespace(
        id=uuid4(),
        type=payload.type,
        name=payload.name,
        name_code=to_snake_case(payload.name),
        finance_id=finance_id,
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
async def test_finance_category_route_create_list() -> None:
    service = AsyncMock()
    payload = SimpleNamespace(categories=[])
    expected = [SimpleNamespace(id="category-id")]
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
async def test_finance_category_route_list_all_paginate_and_filter() -> None:
    service = AsyncMock()
    page_filter = category_filter(page=1, limit=12)
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
async def test_finance_category_route_find_one() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(
        id="category-id",
        name="Test Category",
        type=CategoryTypeEnum.OTHER,
        name_code="test_category",
        finance_id=uuid4(),
        description="Some Description",
    )
    service.find_one_cached.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await find_one(
        param="category-id",
        current_user=current_user,
        service=service,
    )

    assert result is expected
    service.find_one_cached.assert_awaited_once_with(
        param="category-id",
        user_request="Finance User",
        clean_cache=False,
        with_deleted=False,
        finance_id="finance-id",
    )


@pytest.mark.asyncio
async def test_finance_category_route_update() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(
        id="category-id",
        name="Test Category",
        type=CategoryTypeEnum.OTHER,
        name_code="test_category",
        finance_id=uuid4(),
        description="Some Description",
    )
    service.update.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )
    payload = PayloadCategoryUpdateSchema(name="Test Category")
    result = await update(
        param="category-id", current_user=current_user, service=service, payload=payload
    )

    assert result is expected
    service.update.assert_awaited_once_with(
        param="category-id",
        user_request="Finance User",
        update_schema=payload,
    )


@pytest.mark.asyncio
async def test_finance_category_route_delete() -> None:
    service = AsyncMock()
    expected = SimpleNamespace(message="Deleted Account successfully")
    service.soft_delete.return_value = expected
    current_user = SimpleNamespace(
        id="user-id", username="Finance User", finance=SimpleNamespace(id="finance-id")
    )

    result = await delete(
        param="category-id", current_user=current_user, service=service
    )

    assert result is expected
    service.soft_delete.assert_awaited_once_with(
        param="category-id",
        user_request="Finance User",
        finance_id="finance-id",
    )
