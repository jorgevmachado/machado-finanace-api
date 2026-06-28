from __future__ import annotations

import logging
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.account.service import AccountService

from app.domain.finance.allocation.service import AllocationService
from app.domain.finance.category.service import CategoryService
from app.domain.finance.expense.business import validate_paid_at

from app.domain.finance.expense.repository import (
    ExpenseRepository,
)
from app.domain.finance.expense.schema import (
    ExpenseSchema,
    PayloadExpenseCreateSchema,

)

from app.models import Expense, Finance, Account, Allocation, Category

logger = logging.getLogger(__name__)


class ExpenseService(BaseService[ExpenseRepository, Expense]):
    def __init__(
        self,
        repository: ExpenseRepository,
        account_service: AccountService | None = None,
        category_service: CategoryService | None = None,
        allocation_service: AllocationService | None = None,
    ) -> None:
        super().__init__(
            alias="Expense",
            repository=repository,
            logger_params=LoggingParams(
                logger=logger,
                service="ExpenseService",
                operation="expense",
            ),
            schema_class=ExpenseSchema,
            cache_prefix="expense",
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
        return cls(ExpenseRepository(session))

    async def create(
        self, finance: Finance, payload: PayloadExpenseCreateSchema
    ) -> Expense:

        account, allocation = await self._validate_relations(
            finance=finance,
            account_id=payload.account_id,
            allocation_id=payload.allocation_id,
        )

        category = await self._validate_category(payload.category_id, finance.id)
        
        return await self._persist(
            finance=finance,
            account=account,
            allocation=allocation,
            category=category,
            payload=payload,
            with_throw=True
        )

    async def _validate_relations(
        self,
        finance: Finance,
        account_id: UUID,
        allocation_id: UUID,
    ):
        account = await self.account_service.find_by(
            id=account_id, finance_id=finance.id, without_throw=True
        )
        if not account:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Account with this id {account_id} does not exist",
            )

        allocation = await self.allocation_service.find_by(
            id=allocation_id, without_throw=True
        )
        if not allocation:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Allocation with this id {allocation_id} does not exist",
            )

        return account, allocation

    async def _validate_category(self, category_id: UUID, finance_id: UUID) -> Category:
        category = await self.category_service.find_by(
            id=category_id, finance_id=finance_id, without_throw=True
        )
        if not category:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Category {category_id} not found for finance {finance_id}",
            )
        return category
    
    async def _persist(
            self,
            finance: Finance,
            account: Account,
            category: Category,
            allocation: Allocation,            
            payload: PayloadExpenseCreateSchema,
            with_throw: bool = True,
    ) -> Expense:
        expense = await self.find_by(
            finance_id=finance.id,
            account_id=account.id,
            allocation_id=allocation.id,
            category_id=category.id,
            paid_at=payload.paid_at,
            without_throw=True,
        )
        if expense:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail="Expense already exists",
                )
            else:
                expense.amount = payload.amount
                expense.description = payload.description
                expense.paid_at = payload.paid_at
                return await self.repository.update(entity=expense)
            
        else:
            paid_at = validate_paid_at(payload.status, payload.paid_at)

            return await self.repository.save(
                entity=Expense(
                    status=payload.status,
                    amount=payload.amount,
                    paid_at=paid_at,
                    finance_id=finance.id,
                    account_id=payload.account_id,
                    category_id=payload.category_id,
                    description=payload.description,
                    allocation_id=payload.allocation_id
                )
            )