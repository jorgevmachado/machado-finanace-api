from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.domain.auth.repository import UserRepository
from app.domain.auth.schema import RegisterSchema
from app.models.enums import StatusEnum


def build_register_schema() -> RegisterSchema:
    return RegisterSchema(
        name="Ash Ketchum",
        email="ash@example.com",
        username="ash",
        password="pikachu123",
    )


class TestUserRepository:
    @staticmethod
    @pytest.mark.asyncio
    async def test_get_by_variants_delegate_to_scalar() -> None:
        session = AsyncMock()
        repository = UserRepository(session=session)

        await repository.get_by_email("ash@example.com")
        await repository.get_by_username("ash")
        await repository.get_by_email_or_username("ash")

        assert session.scalar.await_count == 3

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_builds_user_and_delegates_to_save() -> None:
        session = AsyncMock()
        repository = UserRepository(session=session)
        expected = SimpleNamespace(id=uuid4())
        repository.save = AsyncMock(return_value=expected)

        result = await repository.create(
            build_register_schema().model_dump() | {"status": StatusEnum.ACTIVE}
        )

        assert result is expected
        repository.save.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_update_methods_execute_and_commit() -> None:
        session = AsyncMock()
        repository = UserRepository(session=session)
        user_id = uuid4()

        await repository.update_status(user_id, StatusEnum.ACTIVE)
        await repository.soft_delete(user_id)

        assert session.execute.await_count == 2
        assert session.commit.await_count == 2
