from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.domain.finance.category.schema import (
    PayloadCategoryCreateSchema,
)
from app.domain.finance.category.service import CategoryService
from app.models import Finance
from app.shared.utils.string import to_snake_case


@pytest.fixture
def finance():
    finance = MagicMock(spec=Finance)
    finance.id = uuid4()
    return finance


@pytest.fixture
def category_repository_mock() -> AsyncMock:
    return AsyncMock()


class TestFinanceCategoryServiceFromSession:
    @staticmethod
    @pytest.mark.asyncio
    async def test_from_session_builds_service() -> None:
        service = CategoryService.from_session(AsyncMock())
        assert isinstance(service, CategoryService)


class TestFinanceCategoryCreateService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_category_create_raises_when_category_exists(
        category_repository_mock: AsyncMock, finance
    ):
        payload = PayloadCategoryCreateSchema(
            name="Test Category",
            description="Some Description",
        )
        service = CategoryService(repository=category_repository_mock)
        service.find_by = AsyncMock(return_value=SimpleNamespace(id=uuid4()))

        with pytest.raises(HTTPException) as exc_info:
            await service.create(finance=finance, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Category with this name {payload.name} already exists"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_category_create_successfully(
        category_repository_mock: AsyncMock, finance
    ):
        payload = PayloadCategoryCreateSchema(
            name="Test Category",
            description="Some Description",
        )
        expected = SimpleNamespace(
            id=uuid4(), name=payload.name, description=payload.description
        )
        service = CategoryService(repository=category_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        category_repository_mock.save.return_value = expected

        result = await service.create(finance=finance, payload=payload)
        assert result == expected
        category_repository_mock.save.assert_awaited_once()
        saved_entity = category_repository_mock.save.await_args.kwargs["entity"]
        assert saved_entity.finance_id == finance.id
        assert saved_entity.name == payload.name
        assert saved_entity.name_code == to_snake_case(payload.name)
        assert saved_entity.description == payload.description


class TestFinanceCategoryPersistService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_category_persist_raises_when_category_exists(
        category_repository_mock: AsyncMock, finance
    ):
        name = "Test Category"
        description = "Some Description"
        service = CategoryService(repository=category_repository_mock)
        service.find_by = AsyncMock(return_value=SimpleNamespace(id=uuid4()))

        with pytest.raises(HTTPException) as exc_info:
            await service.persist(
                name=name,
                finance=finance,
                description=description,
            )

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == f"Category with this name {name} already exists"

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_category_persist_returns_existing_when_with_throw_false(
        category_repository_mock: AsyncMock, finance
    ):

        existing = SimpleNamespace(id=uuid4())
        service = CategoryService(repository=category_repository_mock)
        service.find_by = AsyncMock(return_value=existing)

        result = await service.persist(
            name="Test Category",
            finance=finance,
            description="Some Description",
            with_throw=False,
        )

        assert result is existing
        category_repository_mock.save.assert_not_awaited()

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_category_persist_successfully_saves(
        category_repository_mock: AsyncMock, finance
    ):
        expected = SimpleNamespace(id=uuid4())
        service = CategoryService(repository=category_repository_mock)
        service.find_by = AsyncMock(return_value=None)
        category_repository_mock.save.return_value = expected
        name = "Test Category"
        description = "Some Description"
        result = await service.persist(
            name=name,
            finance=finance,
            description=description,
        )

        assert result is expected
        category_repository_mock.save.assert_awaited_once()
        saved_entity = category_repository_mock.save.await_args.kwargs["entity"]
        assert saved_entity.finance_id == finance.id
        assert saved_entity.name == name
        assert saved_entity.name_code == to_snake_case(name)
        assert saved_entity.description == description
