from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.account.service import AccountService
from app.domain.finance.income.business import validate_year, validate_month
from app.domain.finance.income.repository import IncomeRepository
from app.domain.finance.income.schema import PayloadIncomeCreateSchema, IncomeSchema

from app.models import User, Income
from app.shared.utils.string import to_snake_case

logger = logging.getLogger(__name__)


class IncomeService(BaseService[IncomeRepository, Income]):
    def __init__(
        self,
        repository: IncomeRepository,
        account_service: AccountService | None = None,
    ) -> None:
        super().__init__(
            alias="Income",
            repository=repository,
            logger_params=LoggingParams(
                logger=logger, service="IncomeService", operation="income"
            ),
            schema_class=IncomeSchema,
            cache_prefix="income",
        )
        session = repository.session
        self.account_service = account_service or AccountService.from_session(session)

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(IncomeRepository(session))

    async def create(self, current_user: User, payload: PayloadIncomeCreateSchema) -> Income:
        if not current_user.finance:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="User must be onboarded first",
            )

        reference_year = validate_year(payload.reference_year)
        reference_month = validate_month(payload.reference_month)

        source_code = to_snake_case(payload.source)
        income = await self.find_by(
            finance_id=current_user.finance.id,
            source_code=source_code,
            reference_year=reference_year,
            reference_month=reference_month,
            without_throw=True
        )
        if income:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Income with this year {reference_year}, month {reference_month} and source {payload.source} already exists",
            )

        account = await self.account_service.find_by(id=payload.account_id, without_throw=True)
        if not account:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Account with this id {payload.account_id} does not exist",
            )
        return await self.repository.save(
            entity=Income(
                source=payload.source,
                amount=payload.amount,
                finance_id=current_user.finance.id,
                account_id=account.id,
                source_code=source_code,
                received_at=payload.received_at,
                description=payload.description,
                reference_year=reference_year,
                reference_month=reference_month,
            )
        )    
