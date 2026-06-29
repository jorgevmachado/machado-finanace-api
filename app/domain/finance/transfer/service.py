from __future__ import annotations

import logging
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.account.service import AccountService

from app.domain.finance.transfer.repository import (
    TransferRepository,
)
from app.domain.finance.transfer.schema import (
    TransferSchema,
    PayloadTransferCreateSchema,

)

from app.models import Transfer, Finance, Account

logger = logging.getLogger(__name__)


class TransferService(BaseService[TransferRepository, Transfer]):
    def __init__(
        self,
        repository: TransferRepository,
        account_service: AccountService | None = None,        
    ) -> None:
        super().__init__(
            alias="Transfer",
            repository=repository,
            logger_params=LoggingParams(
                logger=logger,
                service="TransferService",
                operation="transfer",
            ),
            schema_class=TransferSchema,
            cache_prefix="transfer",
        )
        session = repository.session
        self.account_service = account_service or AccountService.from_session(session)        

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(TransferRepository(session))

    async def create(
        self, finance: Finance, payload: PayloadTransferCreateSchema
    ) -> Transfer:

        to_account, from_account = await self._validate_relations(
            finance=finance,
            to_account_id=payload.to_account_id,            
            from_account_id=payload.from_account_id,            
        )
        
        return await self._persist(
            finance=finance,
            to_account=to_account,
            from_account=from_account,            
            payload=payload,
            with_throw=True
        )

    async def _validate_relations(
        self,
        finance: Finance,
        to_account_id: UUID,
        from_account_id: UUID,
    ):
        to_account = await self.account_service.find_by(
            id=to_account_id, finance_id=finance.id, without_throw=True
        )
        if not to_account:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"To Account with this id {to_account_id} does not exist",
            )

        from_account = await self.account_service.find_by(
            id=from_account_id, finance_id=finance.id, without_throw=True
        )
        if not from_account:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"From Account with this id {from_account_id} does not exist",
            )

        return to_account, from_account
    
    async def _persist(
            self,
            finance: Finance,
            to_account: Account,
            from_account: Account,                        
            payload: PayloadTransferCreateSchema,
            with_throw: bool = True,
    ) -> Transfer:
        transfer = await self.find_by(
            finance_id=finance.id,
            to_account_id=to_account.id,
            from_account_id=from_account.id,            
            transfer_date=payload.transfer_date,
            without_throw=True,
        )
        if transfer:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail="Transfer already exists",
                )
            else:
                transfer.amount = payload.amount
                transfer.description = payload.description
                transfer.transfer_date = payload.transfer_date
                return await self.repository.update(entity=transfer)
            
        else:            
            return await self.repository.save(
                entity=Transfer(
                    amount=payload.amount,
                    finance_id=finance.id,
                    description=payload.description,
                    transfer_date=payload.transfer_date,
                    to_account_id=to_account.id,
                    from_account_id=from_account.id,
                )
            )