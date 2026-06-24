from __future__ import annotations

import logging
from datetime import date
from http import HTTPStatus
from uuid import UUID

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
    TransactionSchema, PayloadTransactionCreateListSchema, PayloadTransactionCreateListCategoryItemSchema,
)

from app.models import Transaction, Finance, utcnow, Account, Allocation, Category
from app.shared.utils.date import get_valid_day, generate_description
from app.shared.utils.validator import validate_year, validate_month

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

    async def create_list(
            self,
            finance: Finance,
            payload: PayloadTransactionCreateListSchema,
    ) -> list[Transaction]:
        account, allocation = await self._validate_relations(
            finance=finance,
            account_id=payload.account_id,
            allocation_id=payload.allocation_id,
        )

        payload_categories = payload.categories if payload.categories else []

        if len(payload_categories) == 0:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Transaction category list cannot be empty",
            )
        current_date = utcnow()
        year = payload.reference_year if payload.reference_year else current_date.year
        reference_year = validate_year(year)

        final_transactions: list[Transaction] = []
        if payload_categories and len(payload_categories) > 0:
            for category_item in payload_categories:
                category_transactions = await self._persist_by_category(
                    finance=finance,
                    payload=category_item,
                    account=account,
                    allocation=allocation,
                    reference_year=reference_year,
                    reference_day=payload.reference_day
                )
                if category_transactions and len(category_transactions) > 0:
                    final_transactions.extend(category_transactions)

        return final_transactions

    async def _persist_by_category(
        self,
        finance: Finance,
        payload: PayloadTransactionCreateListCategoryItemSchema,
        account: Account,
        allocation: Allocation,
        reference_year: int,
        reference_day: int | None = None,
    ) -> list[Transaction]:
        transactions: list[Transaction] = []
        payload_transactions = payload.transactions if payload.transactions else []
        if payload_transactions and len(payload_transactions) <= 0 or len(payload_transactions) > 12:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Invalid number of transactions for category {payload.category_id}. Must be between 1 and 12.",
            )
        
        category = await self._validate_category(payload.category_id, finance.id)
        base_day = payload.reference_day if payload.reference_day else reference_day
        for item in payload_transactions:
            reference_month = validate_month(item.reference_month)
            print('# => reference_month => ', reference_month)
            transaction_day = get_valid_day(
                year=reference_year,
                month=reference_month,
                day=base_day,
            )

            transaction_date = (
                item.transaction_date
                if item.transaction_date
                else date(reference_year, reference_month, transaction_day)
            )
            print("# => payload => description => ", payload.description)
            description = generate_description(
                month=reference_month,
                source="transaction",
                item_description=payload.description,
            )
            print("# => description => ", description)
            print("# => transaction_date => ", transaction_date)

            payload_transaction_create = PayloadTransactionCreateSchema(
                type=payload.type,
                status=item.status,
                amount=item.amount,
                paid_at=item.paid_at,
                account_id=account.id,
                category_id=category.id,
                description=description,
                allocation_id=allocation.id,
                transaction_date=transaction_date,
            )

            transaction = await self._persist(
                finance=finance,
                account=account,
                category=category,
                allocation=allocation,
                payload=payload_transaction_create,
                with_throw=False,
            )

            transactions.append(transaction)
        
        return transactions

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
            payload: PayloadTransactionCreateSchema,
            with_throw: bool = True,
    ) -> Transaction:
        transaction = await self.find_by(
            finance_id=finance.id,
            account_id=account.id,
            allocation_id=allocation.id,
            category_id=category.id,
            transaction_date=payload.transaction_date,
            without_throw=True,
        )
        if transaction:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail="Transaction already exists",
                )
            else:
                transaction.amount = payload.amount
                transaction.description = payload.description
                transaction.transaction_date = payload.transaction_date
                return await self.repository.update(entity=transaction)
            
        else:
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