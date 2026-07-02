from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.domain.auth.schema import LoginSchema, RegisterSchema
from app.domain.auth.service import AuthService
from app.models.enums import StatusEnum


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
def mock_repository():
    return AsyncMock()


class TestAuthServiceRegister:
    @pytest.mark.asyncio
    async def test_register_rejects_existing_email(self, mock_repository, register_schema):
        mock_repository.get_by_email.return_value = SimpleNamespace(id=uuid4())
        service = AuthService(repository=mock_repository)

        with pytest.raises(HTTPException) as exc_info:
            await service.register(register_schema)

        assert exc_info.value.status_code == HTTPStatus.CONFLICT
        assert exc_info.value.detail == "Email already registered"
        mock_repository.get_by_email.assert_awaited_once_with(register_schema.email)

    @pytest.mark.asyncio
    async def test_register_rejects_existing_username(self, mock_repository, register_schema):
        mock_repository.get_by_email.return_value = None
        mock_repository.get_by_username.return_value = SimpleNamespace(id=uuid4())
        service = AuthService(repository=mock_repository)

        with pytest.raises(HTTPException) as exc_info:
            await service.register(register_schema)

        assert exc_info.value.status_code == HTTPStatus.CONFLICT
        assert exc_info.value.detail == "Username already taken"
        mock_repository.get_by_email.assert_awaited_once()
        mock_repository.get_by_username.assert_awaited_once_with(register_schema.username)

    @pytest.mark.asyncio
    async def test_register_creates_hashed_user(self, mock_repository, register_schema, monkeypatch):
        user_id = uuid4()
        created_user = SimpleNamespace(id=user_id, email=register_schema.email)
        
        mock_repository.get_by_email.return_value = None
        mock_repository.get_by_username.return_value = None
        mock_repository.create.return_value = created_user
        
        monkeypatch.setattr(
            "app.domain.auth.service.get_password_hash", lambda _: "hashed-password"
        )
        service = AuthService(repository=mock_repository)

        result = await service.register(register_schema)

        assert result is created_user
        assert result.id == user_id
        mock_repository.create.assert_awaited_once()
        
        payload = mock_repository.create.await_args.args[0]
        assert payload["password"] == "hashed-password"
        assert payload["status"] == StatusEnum.ACTIVE
        assert payload["email"] == register_schema.email
        assert payload["username"] == register_schema.username

    @pytest.mark.asyncio
    async def test_register_calls_repository_with_correct_payload(self, mock_repository, register_schema, monkeypatch):
        created_user = SimpleNamespace(id=uuid4())
        mock_repository.get_by_email.return_value = None
        mock_repository.get_by_username.return_value = None
        mock_repository.create.return_value = created_user
        
        monkeypatch.setattr(
            "app.domain.auth.service.get_password_hash", lambda _: "hashed"
        )
        service = AuthService(repository=mock_repository)

        await service.register(register_schema)

        payload = mock_repository.create.await_args.args[0]
        assert payload["name"] == register_schema.name
        assert payload["email"] == register_schema.email
        assert payload["username"] == register_schema.username


class TestAuthServiceLogin:
    @pytest.mark.asyncio
    async def test_login_rejects_missing_user(self, mock_repository, login_schema):
        mock_repository.get_by_email_or_username.return_value = None
        service = AuthService(repository=mock_repository)

        with pytest.raises(HTTPException) as exc_info:
            await service.login(login_schema)

        assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED
        assert exc_info.value.detail == "Invalid credentials"
        mock_repository.get_by_email_or_username.assert_awaited_once_with(
            login_schema.credential
        )

    @pytest.mark.asyncio
    async def test_login_rejects_invalid_password(self, mock_repository, login_schema, monkeypatch):
        user = SimpleNamespace(id=uuid4(), password="hashed", username="ash")
        mock_repository.get_by_email_or_username.return_value = user
        monkeypatch.setattr("app.domain.auth.service.verify_password", lambda *_: False)
        service = AuthService(repository=mock_repository)

        with pytest.raises(HTTPException) as exc_info:
            await service.login(login_schema)

        assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED
        assert exc_info.value.detail == "Invalid credentials"

    @pytest.mark.asyncio
    async def test_login_returns_valid_token(self, mock_repository, login_schema, monkeypatch):
        user_id = uuid4()
        user = SimpleNamespace(id=user_id, password="hashed", role="USER", username="ash")
        mock_repository.get_by_email_or_username.return_value = user
        
        monkeypatch.setattr("app.domain.auth.service.verify_password", lambda *_: True)
        monkeypatch.setattr(
            "app.domain.auth.service.create_access_token",
            lambda payload: f"token-{payload['sub']}",
        )
        service = AuthService(repository=mock_repository)

        result = await service.login(login_schema)

        assert result.access_token == f"token-{user_id}"
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_login_with_email_credential(self, mock_repository, monkeypatch):
        user_id = uuid4()
        email = "user@example.com"
        user = SimpleNamespace(id=user_id, password="hashed", role="USER")
        
        mock_repository.get_by_email_or_username.return_value = user
        monkeypatch.setattr("app.domain.auth.service.verify_password", lambda *_: True)
        monkeypatch.setattr(
            "app.domain.auth.service.create_access_token",
            lambda payload: f"token-{payload['sub']}",
        )
        service = AuthService(repository=mock_repository)

        result = await service.login(LoginSchema(credential=email, password="pass123"))

        mock_repository.get_by_email_or_username.assert_awaited_once_with(email)
        assert result.access_token == f"token-{user_id}"
