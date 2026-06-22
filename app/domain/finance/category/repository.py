from __future__ import annotations

from app.core.repository.base import BaseRepository
from app.models import (
    Category,
)


class CategoryRepository(BaseRepository[Category]):
    model = Category
