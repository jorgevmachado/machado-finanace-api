from __future__ import annotations

from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user

from app.domain.finance.repository import FinanceRepository
from app.domain.finance.schema import FinanceSchema
from app.domain.finance.service import FinanceService
from app.models import User
from app.domain.finance.account.route import router as account_router

router = APIRouter()

router.include_router(account_router, prefix="/account", tags=["FinanceAccount"])

Session = Annotated[AsyncSession, Depends(get_session)]


def finance_service(session: Session) -> FinanceService:
    return FinanceService(FinanceRepository(session))


Service = Annotated[FinanceService, Depends(finance_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post(
    "/onboarding", response_model=FinanceSchema, status_code=HTTPStatus.CREATED
)
async def onboarding(service: Service, current_user: CurrentUser):
    return await service.onboard(current_user=current_user)
