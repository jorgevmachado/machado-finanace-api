from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.account.service import AccountService

from app.domain.finance.allocation.service import AllocationService
from app.domain.finance.category.service import CategoryService
from app.domain.finance.transaction.business import validate_paid_at

from app.domain.finance.transaction.repository import (
    TransactionRepository,
)
from app.domain.finance.transaction.schema import (
    PayloadTransactionCreateSchema,
    TransactionSchema,
)

from app.models import Transaction, Finance

logger = logging.getLogger(__name__)


class TransactionService(BaseService[TransactionRepository, Transaction]):
    def __init__(
        self,
        repository: TransactionRepository,
        account_service: AccountService | None = None,
        category_service: CategoryService | None = None,
        allocation_service: AllocationService | None = None,
    ) -> None:
        super().__init__(
            alias="Transaction",
            repository=repository,
            logger_params=LoggingParams(
                logger=logger,
                service="TransactionService",
                operation="transaction",
            ),
            schema_class=TransactionSchema,
            cache_prefix="transaction",
        )
        session = repository.session
        self.account_service = account_service or AccountService.from_session(session)
        self.category_service = category_service or CategoryService.from_session(
            session
        )
        self.allocation_service = allocation_service or AllocationService.from_session(
            session
        )

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(TransactionRepository(session))

    async def create(
        self, finance: Finance, payload: PayloadTransactionCreateSchema
    ) -> Transaction:
        transaction = await self.find_by(
            finance_id=finance.id,
            account_id=payload.account_id,
            allocation_id=payload.allocation_id,
            category_id=payload.category_id,
            without_throw=True,
        )
        if transaction:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Transaction already exists",
            )

        account = await self.account_service.find_by(
            id=payload.account_id, without_throw=True
        )
        if not account:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Account with this id {payload.account_id} does not exist",
            )

        allocation = await self.allocation_service.find_by(
            id=payload.allocation_id, without_throw=True
        )
        if not allocation:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Allocation with this id {payload.allocation_id} does not exist",
            )

        category = await self.category_service.find_by(
            id=payload.category_id, without_throw=True
        )
        if not category:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Category with this id {payload.category_id} does not exist",
            )

        paid_at = validate_paid_at(payload.status, payload.paid_at)

        return await self.repository.save(
            entity=Transaction(
                type=payload.type,
                status=payload.status,
                amount=payload.amount,
                paid_at=paid_at,
                finance_id=finance.id,
                account_id=payload.account_id,
                category_id=payload.category_id,
                description=payload.description,
                allocation_id=payload.allocation_id,
                transaction_date=payload.transaction_date,
            )
        )
