from __future__ import annotations

from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.pagination import CustomLimitOffsetPage
from app.core.security import get_current_user
from app.core.security.security import validate_finance

from app.domain.finance.income.repository import IncomeRepository
from app.domain.finance.income.schema import (
    IncomeSchema,
    PayloadIncomeCreateSchema,
    PayloadIncomeUpdateSchema,
    PayloadIncomeCreateListSchema,
)
from app.domain.finance.income.service import IncomeService
from app.models import User
from app.shared.schemas import FilterPage, Message

router = APIRouter()

Session = Annotated[AsyncSession, Depends(get_session)]


def income_service(session: Session) -> IncomeService:
    return IncomeService(IncomeRepository(session))


Service = Annotated[IncomeService, Depends(income_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def income_filter(
    page: int | None = None,
    source: str | None = None,
    limit: int | None = 12,
    offset: int | None = None,
    account_id: str | None = None,
    source_code: str | None = None,
    clean_cache: bool = False,
    with_deleted: bool = False,
    reference_year: int | None = None,
    reference_month: int | None = None,
) -> FilterPage:
    return FilterPage.build(
        page=page,
        source=source,
        limit=limit,
        offset=offset,
        account_id=account_id,
        source_code=source_code,
        clean_cache=clean_cache,
        with_deleted=with_deleted,
        reference_year=reference_year,
        reference_month=reference_month,
    )


@router.get(
    "",
    response_model=CustomLimitOffsetPage[IncomeSchema] | list[IncomeSchema],
    status_code=HTTPStatus.OK,
)
async def list_all(
    service: Service,
    current_user: CurrentUser,
    page_filter: Annotated[FilterPage, Depends(income_filter)] = None,
):
    finance = validate_finance(current_user.finance)
    return await service.list_all_cached(
        page_filter=FilterPage.build(
            page_filter=page_filter, finance_id=str(finance.id)
        ),
        user_request=current_user.username,
    )


@router.get("/{param}", response_model=IncomeSchema, status_code=HTTPStatus.OK)
async def find_one(
    param: str,
    service: Service,
    current_user: CurrentUser,
    clean_cache: bool = False,
    with_deleted: bool = False,
):
    finance = validate_finance(current_user.finance)
    return await service.find_one_cached(
        param=param,
        user_request=current_user.username,
        clean_cache=clean_cache,
        with_deleted=with_deleted,
        finance_id=str(finance.id),
    )


@router.post("", response_model=IncomeSchema, status_code=HTTPStatus.CREATED)
async def create(
    service: Service, current_user: CurrentUser, payload: PayloadIncomeCreateSchema
):
    finance = validate_finance(current_user.finance)
    return await service.create(finance=finance, payload=payload)


@router.put("/{param}", response_model=IncomeSchema, status_code=HTTPStatus.CREATED)
async def update(
    param: str,
    service: Service,
    current_user: CurrentUser,
    payload: PayloadIncomeUpdateSchema,
):
    validate_finance(current_user.finance)
    return await service.update(
        param=param, user_request=current_user.username, update_schema=payload
    )


@router.delete("/{param}", response_model=Message, status_code=HTTPStatus.OK)
async def delete(
    param: str,
    service: Service,
    current_user: CurrentUser,
):
    finance = validate_finance(current_user.finance)
    return await service.soft_delete(
        param=param, user_request=current_user.username, finance_id=str(finance.id)
    )


@router.post("/year", response_model=list[IncomeSchema], status_code=HTTPStatus.CREATED)
async def create_list_by_year(
    service: Service, current_user: CurrentUser, payload: PayloadIncomeCreateListSchema
):
    finance = validate_finance(current_user.finance)
    return await service.create_list_by_year(finance=finance, payload=payload)
