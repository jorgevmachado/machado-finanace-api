from __future__ import annotations

import logging

from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.account.business import sum_amounts, sum_expenses_by_status
from app.domain.finance.account.repository import AccountRepository
from app.domain.finance.account.schema import PayloadAccountCreateSchema, AccountSchema
from app.shared.utils.string import to_snake_case

from app.models import (
    Account,
    Finance,
    MonthStatusEnum,
    AccountTypeEnum,
)

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
        return await self.persist(
            name=payload.name,
            type=payload.type,
            finance=finance,
            initial_balance=payload.initial_balance,
            current_balance=payload.current_balance or 0,
        )

    async def persist(
        self,
        name: str,
        type: AccountTypeEnum,
        finance: Finance,
        initial_balance: float,
        current_balance: float  = 0,
        with_throw: bool = True,
    ) -> Account:

        name_code = to_snake_case(name)

        account = await self.find_by(
            name_code=name_code, finance_id=finance.id, without_throw=True
        )

        if account:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Account with this name {name} already exists",
                )
            else:
                return account
        else:
            return await self.repository.save(
                entity=Account(
                    name=name,
                    name_code=name_code,
                    type=type,
                    is_active=True,
                    finance_id=finance.id,
                    initial_balance=initial_balance,
                    current_balance=current_balance,
                )
            )

    async def recalculate(self, param: str, finance: Finance) -> Account:
        entity = await self.find_one(param=param, finance_id=finance.id)

        income = sum_amounts(income.amount for income in (entity.incomes or []))
        incoming_transfer = sum_amounts(
            incoming_transfer.amount
            for incoming_transfer in (entity.incoming_transfers or [])
        )
        outgoing_transfer = sum_amounts(
            outgoing_transfer.amount
            for outgoing_transfer in (entity.outgoing_transfers or [])
        )
        expenses = entity.expenses if entity.expenses else []
        total_paid = sum_expenses_by_status(expenses, MonthStatusEnum.PAID)

        total_spend = total_paid + outgoing_transfer
        total_income = sum_amounts((entity.initial_balance, income, incoming_transfer))
        current_balance = total_income - total_spend

        if entity.current_balance != current_balance:
            entity.current_balance = current_balance
            return await self.update_entity(entity=entity)
        return entity
