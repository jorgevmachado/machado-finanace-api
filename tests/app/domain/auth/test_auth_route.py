from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.domain.auth.route import get_auth_service, login, me, register
from app.domain.auth.schema import LoginSchema, RegisterSchema
from app.domain.auth.service import AuthService
from app.models.enums import StatusEnum, RoleEnum


@pytest.fixture
def register_schema():
    return RegisterSchema(
        name="Ash Ketchum",
        email="ash@example.com",
        username="ash",
        password="pikachu123",
    )


@pytest.fixture
def login_schema():
    return LoginSchema(credential="ash", password="pikachu123")


@pytest.fixture
def mock_service():
    return AsyncMock(spec=AuthService)


class TestAuthRoutes:
    def test_get_auth_service_builds_service(self):
        service = get_auth_service(AsyncMock())
        assert isinstance(service, AuthService)

    @pytest.mark.asyncio
    async def test_register_route_calls_service(self, mock_service, register_schema):
        user_id = uuid4()
        expected_result = SimpleNamespace(id=user_id, email=register_schema.email)
        mock_service.register.return_value = expected_result

        result = await register(register_schema, service=mock_service)

        assert result is expected_result
        mock_service.register.assert_awaited_once_with(register_schema)

    @pytest.mark.asyncio
    async def test_register_route_returns_user_response(self, mock_service, register_schema):
        created_user = SimpleNamespace(
            id=uuid4(),
            name=register_schema.name,
            email=register_schema.email,
            username=register_schema.username,
        )
        mock_service.register.return_value = created_user

        result = await register(register_schema, service=mock_service)

        assert result.id == created_user.id
        assert result.name == register_schema.name

    @pytest.mark.asyncio
    async def test_login_route_returns_valid_token(self, mock_service, login_schema):
        mock_service.login.return_value = SimpleNamespace(
            access_token="token-123", token_type="bearer"
        )

        result = await login(login_schema, service=mock_service)

        assert result.access_token == "token-123"
        assert result.token_type == "bearer"
        mock_service.login.assert_awaited_once_with(login_schema)

    @pytest.mark.asyncio
    async def test_login_route_delegates_credential_to_service(self, mock_service):
        login_data = LoginSchema(credential="user@example.com", password="secret")
        mock_service.login.return_value = SimpleNamespace(
            access_token="token", token_type="bearer"
        )

        await login(login_data, service=mock_service)

        mock_service.login.assert_awaited_once_with(login_data)

    @pytest.mark.asyncio
    async def test_me_route_returns_current_user(self):
        user_id = uuid4()
        current_user = SimpleNamespace(
            id=user_id,
            name="Ash",
            email="ash@example.com",
            username="ash",
            role=RoleEnum.USER,
            status=StatusEnum.ACTIVE,
            created_at=datetime.now(timezone.utc),
        )

        result = await me(current_user=current_user)

        assert result is current_user
        assert result.id == user_id
        assert result.email == "ash@example.com"

    @pytest.mark.asyncio
    async def test_me_route_preserves_user_attributes(self):
        user_id = uuid4()
        created_at = datetime.now(timezone.utc)
        current_user = SimpleNamespace(
            id=user_id,
            name="Trainer",
            email="trainer@example.com",
            username="trainer",
            role=RoleEnum.ADMIN,
            status=StatusEnum.ACTIVE,
            created_at=created_at,
        )

        result = await me(current_user=current_user)

        assert result.name == "Trainer"
        assert result.role == RoleEnum.ADMIN
        assert result.status == StatusEnum.ACTIVE
