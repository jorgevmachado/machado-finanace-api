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
from app.domain.finance.allocation.route import router as allocation_route
from app.domain.finance.income.route import router as income_route
from app.domain.finance.allocation_contribution.route import (
    router as allocation_contribution_route,
)
from app.domain.finance.category.route import router as category_route
from app.domain.finance.expense.route import router as expense_route

router = APIRouter()

router.include_router(account_router, prefix="/accounts", tags=["FinanceAccount"])

router.include_router(
    allocation_route, prefix="/allocations", tags=["FinanceAllocation"]
)

router.include_router(income_route, prefix="/incomes", tags=["FinanceIncome"])

router.include_router(
    allocation_contribution_route,
    prefix="/allocation-contributions",
    tags=["FinanceAllocationContribution"],
)

router.include_router(category_route, prefix="/categories", tags=["FinanceCategory"])

router.include_router(
    expense_route, prefix="/expenses", tags=["FinanceExpense"]
)

Session = Annotated[AsyncSession, Depends(get_session)]


def finance_service(session: Session) -> FinanceService:
    return FinanceService(FinanceRepository(session))


Service = Annotated[FinanceService, Depends(finance_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("", response_model=FinanceSchema, status_code=HTTPStatus.OK)
async def find_by_user(service: Service, current_user: CurrentUser):
    return await service.find_by_user(current_user=current_user)


@router.post(
    "/onboarding", response_model=FinanceSchema, status_code=HTTPStatus.CREATED
)
async def onboarding(service: Service, current_user: CurrentUser):
    return await service.onboard(current_user=current_user)
