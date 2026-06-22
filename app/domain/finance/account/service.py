from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.account.repository import AccountRepository
from app.domain.finance.account.schema import PayloadAccountCreateSchema, AccountSchema
from app.shared.utils.string import to_snake_case

from app.models import User, Account

logger = logging.getLogger(__name__)


class AccountService(BaseService[AccountRepository, Account]):
    def __init__(
        self,
        repository: AccountRepository,
    ) -> None:
        super().__init__(
            alias="Account",
            repository=repository,
            logger_params=LoggingParams(
                logger=logger, service="AccountService", operation="account"
            ),
            schema_class=AccountSchema,
            cache_prefix="account",
        )

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(AccountRepository(session))

    async def create(
        self, current_user: User, payload: PayloadAccountCreateSchema
    ) -> Account:
        if not current_user.finance:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="User must be onboarded first",
            )
        account = await self.find_by(
            finance_id=current_user.finance.id, name=payload.name, without_throw=True
        )
        if account:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Account with this name already exists",
            )

        return await self.repository.save(
            entity=Account(
                finance_id=current_user.finance.id,
                name=payload.name,
                name_code=to_snake_case(payload.name),
                type=payload.type,
                is_active=True,
                initial_balance=payload.initial_balance,
                current_balance=payload.initial_balance,
            )
        )
