from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.account.repository import AccountRepository
from app.domain.finance.account.schema import (
    PayloadAccountCreateSchema,
    AccountSchema,
    PayloadAccountCreateListSchema,
)
from app.shared.utils.string import to_snake_case

from app.models import Account, Finance

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
        self, finance: Finance, payload: PayloadAccountCreateSchema
    ) -> Account:
        return await self.persist(finance=finance, payload=payload)

    async def create_list(
        self, finance: Finance, payload: PayloadAccountCreateListSchema
    ) -> list[Account]:
        payload_accounts = payload.accounts if payload.accounts else []
        if len(payload_accounts) == 0:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Accounts list cannot be empty",
            )

        accounts: list[Account] = []
        if payload_accounts and len(payload_accounts) > 0:
            for item in payload_accounts:
                account = await self.persist(
                    finance=finance, payload=item, with_throw=False
                )
                accounts.append(account)
        return accounts

    async def persist(
        self,
        finance: Finance,
        payload: PayloadAccountCreateSchema,
        with_throw: bool = True,
    ) -> Account:

        account = await self.find_by(
            finance_id=finance.id, name=payload.name, without_throw=True
        )

        if account:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Account with this name {payload.name} already exists",
                )
            else:
                return account
        else:
            return await self.repository.save(
                entity=Account(
                    finance_id=finance.id,
                    name=payload.name,
                    name_code=to_snake_case(payload.name),
                    type=payload.type,
                    is_active=True,
                    initial_balance=payload.initial_balance,
                    current_balance=payload.initial_balance,
                )
            )
