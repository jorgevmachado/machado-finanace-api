from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domain.auth.schema import RegisterSchema


def test_register_schema_rejects_short_password() -> None:
    with pytest.raises(ValidationError):
        RegisterSchema(
            name="Ash",
            email="ash@example.com",
            username="ash",
            password="short",
        )
