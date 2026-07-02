from __future__ import annotations

from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.core.security.security import validate_finance

from app.domain.finance.plan.schema import PayloadPlanCreateSchema, PlanSchema
from app.domain.finance.plan.service import PlanService
from app.domain.finance.repository import FinanceRepository
from app.models import User

router = APIRouter()

Session = Annotated[AsyncSession, Depends(get_session)]


def plan_service(session: Session) -> PlanService:
    return PlanService(FinanceRepository(session))


Service = Annotated[PlanService, Depends(plan_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("", response_model=PlanSchema, status_code=HTTPStatus.CREATED)
async def create(
    service: Service, current_user: CurrentUser, payloads: list[PayloadPlanCreateSchema]
):
    finance = validate_finance(current_user.finance)
    return await service.create(finance=finance, payloads=payloads)
