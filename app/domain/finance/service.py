from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.repository import FinanceRepository
from app.domain.finance.schema import FinanceSchema

from app.models import (
    User,
    Finance,
)

logger = logging.getLogger(__name__)


class FinanceService(BaseService[FinanceRepository, Finance]):
    def __init__(
        self,
        repository: FinanceRepository,
    ) -> None:
        super().__init__(
            alias="Finance",
            repository=repository,
            logger_params=LoggingParams(
                logger=logger, service="FinanceService", operation="finance"
            ),
            schema_class=FinanceSchema,
            cache_prefix="finance",
        )

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(FinanceRepository(session))

    async def onboard(self, current_user: User) -> Finance:
        if current_user.finance:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"User {current_user.username} already onboarded",
            )
        return await self.repository.save(entity=Finance(user_id=current_user.id))

    async def find_by_user(self, current_user: User) -> Finance:
        finance = current_user.finance if current_user.finance else None
        if not finance:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"User {current_user.username} must be onboarded first",
            )
        return await self.find_one(param=str(finance.id))
