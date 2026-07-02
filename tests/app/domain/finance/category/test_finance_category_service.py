from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.domain.finance.category.schema import (
    PayloadCategoryCreateListSchema,
    PayloadCategoryCreateSchema,
)
from app.domain.finance.category.service import CategoryService
from app.models import CategoryTypeEnum
from app.shared.utils.string import to_snake_case


@pytest.fixture
def category_repository_mock() -> AsyncMock:
    return AsyncMock()


class TestFinanceCategoryServiceFromSession:
    @staticmethod
    @pytest.mark.asyncio
    async def test_from_session_builds_service() -> None:
        service = CategoryService.from_session(AsyncMock())
        assert isinstance(service, CategoryService)


class TestFinanceCategoryPersistService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_raises_when_category_exists(
        category_repository_mock: AsyncMock,
    ):
        payload = PayloadCategoryCreateSchema(
            name="Test Category",
            type=CategoryTypeEnum.OTHER,
            description="Some Description",
        )
        finance = SimpleNamespace(id=uuid4())
        service = CategoryService(repository=category_repository_mock)
        service.find_by = AsyncMock(return_value=SimpleNamespace(id=uuid4()))

        with pytest.raises(HTTPException) as exc_info:
            await service.persist(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Category with this name {payload.name} already exists"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_returns_existing_when_with_throw_false(
        category_repository_mock: AsyncMock,
    ):
        payload = PayloadCategoryCreateSchema(
            name="Test Category",
            type=CategoryTypeEnum.OTHER,
            description="Some Description",
        )
        finance = SimpleNamespace(id=uuid4())
        existing = SimpleNamespace(id=uuid4())
        service = CategoryService(repository=category_repository_mock)
        service.find_by = AsyncMock(return_value=existing)

        result = await service.persist(
            finance=finance, payload=payload, with_throw=False
        )

        assert result is existing
        category_repository_mock.save.assert_not_awaited()

    @staticmethod
    @pytest.mark.asyncio
    async def test_persist_successfully_saves(category_repository_mock: AsyncMock):
        payload = PayloadCategoryCreateSchema(
            name="Test Category",
            type=CategoryTypeEnum.OTHER,
            description="Some Description",
        )
        finance_id = uuid4()
        finance = SimpleNamespace(id=finance_id)
        expected = SimpleNamespace(id=uuid4())
        service = CategoryService(repository=category_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        category_repository_mock.save.return_value = expected

        result = await service.persist(finance=finance, payload=payload)

        assert result is expected
        category_repository_mock.save.assert_awaited_once()
        saved_entity = category_repository_mock.save.await_args.kwargs["entity"]
        assert saved_entity.finance_id == finance_id
        assert saved_entity.name == payload.name
        assert saved_entity.name_code == to_snake_case(payload.name)
        assert saved_entity.type == payload.type
        assert saved_entity.description == payload.description

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_list_raises_for_empty_payload(
        category_repository_mock: AsyncMock,
    ):
        service = CategoryService(repository=category_repository_mock)
        payload = PayloadCategoryCreateListSchema(categories=[])

        with pytest.raises(HTTPException) as exc_info:
            await service.create_list(
                finance=SimpleNamespace(id=uuid4()), payload=payload
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "Categories list cannot be empty"

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_list_calls_persist_for_each_item(
        category_repository_mock: AsyncMock,
    ):
        service = CategoryService(repository=category_repository_mock)
        finance = SimpleNamespace(id=uuid4())
        payload = PayloadCategoryCreateListSchema(
            categories=[
                PayloadCategoryCreateSchema(
                    name="Alimentacao",
                    type=CategoryTypeEnum.FOOD,
                    description="Comidas",
                ),
                PayloadCategoryCreateSchema(
                    name="Casa",
                    type=CategoryTypeEnum.OTHER,
                    description="Despesas da casa",
                ),
            ]
        )
        expected = [SimpleNamespace(id=uuid4()), SimpleNamespace(id=uuid4())]
        service.persist = AsyncMock(side_effect=expected)

        result = await service.create_list(finance=finance, payload=payload)

        assert result == expected
        assert service.persist.await_count == 2
        first_call = service.persist.await_args_list[0].kwargs
        second_call = service.persist.await_args_list[1].kwargs
        assert first_call["finance"] is finance
        assert first_call["payload"] == payload.categories[0]
        assert first_call["with_throw"] is False
        assert second_call["payload"] == payload.categories[1]
