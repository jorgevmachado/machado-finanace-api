from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4


import pytest
from fastapi import HTTPException

from app.domain.finance.category.schema import PayloadCategoryCreateSchema
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


class TestFinanceCategoryCreateService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_category_service_create_not_has_finance(
        category_repository_mock: AsyncMock,
    ):
        payload = PayloadCategoryCreateSchema(
            name="Test Category",
            type=CategoryTypeEnum.OTHER,
            description="Some Description",
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=None
        )

        service = CategoryService(repository=category_repository_mock)

        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert exc_info.value.detail == "User must be onboarded first"

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_category_service_create_already_exist_account(
        category_repository_mock: AsyncMock,
    ):
        payload = PayloadCategoryCreateSchema(
            name="Test Category",
            type=CategoryTypeEnum.OTHER,
            description="Some Description",
        )
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=uuid4())
        )

        service = CategoryService(repository=category_repository_mock)
        service.find_by = AsyncMock(return_value=SimpleNamespace(id=uuid4()))

        with pytest.raises(HTTPException) as exc_info:
            await service.create(current_user=current_user, payload=payload)

        assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
        assert (
            exc_info.value.detail
            == f"Category with this name {payload.name} already exists"
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_finance_category_service_create_successfully(
        category_repository_mock: AsyncMock,
    ):
        payload = PayloadCategoryCreateSchema(
            name="Test Category",
            type=CategoryTypeEnum.OTHER,
            description="Some Description",
        )
        finance_id = uuid4()
        current_user = SimpleNamespace(
            id=uuid4(), username="Finance User", finance=SimpleNamespace(id=finance_id)
        )
        category = SimpleNamespace(
            id=uuid4(),
            finance_id=finance_id,
            name=payload.name,
            name_code=to_snake_case(payload.name),
            type=payload.type,
            description=payload.description,
        )

        service = CategoryService(repository=category_repository_mock)
        service.find_by = AsyncMock(return_value=None)

        category_repository_mock.save.return_value = category

        result = await service.create(current_user=current_user, payload=payload)
        category_repository_mock.save.assert_awaited_once()
        assert result == category
