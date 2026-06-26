from __future__ import annotations

from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.pagination import CustomLimitOffsetPage
from app.core.security import get_current_user
from app.core.security.security import validate_finance

from app.domain.finance.account.repository import AccountRepository
from app.domain.finance.account.schema import (
    AccountSchema,
    PayloadAccountCreateSchema,
    PayloadAccountUpdateSchema,
    PayloadAccountCreateListSchema,
)
from app.domain.finance.account.service import AccountService
from app.models import User
from app.shared.schemas import FilterPage, Message

router = APIRouter()

Session = Annotated[AsyncSession, Depends(get_session)]


def account_service(session: Session) -> AccountService:
    return AccountService(AccountRepository(session))


Service = Annotated[AccountService, Depends(account_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def account_filter(
    page: int | None = None,
    name: str | None = None,
    type: str | None = None,
    limit: int | None = 12,
    offset: int | None = None,
    is_active: bool | None = None,
    clean_cache: bool = False,
    with_deleted: bool = False,
) -> FilterPage:
    return FilterPage.build(
        page=page,
        name=name,
        type=type,
        limit=limit,
        offset=offset,
        is_active=is_active,
        clean_cache=clean_cache,
        with_deleted=with_deleted,
    )


@router.get(
    "",
    response_model=CustomLimitOffsetPage[AccountSchema] | list[AccountSchema],
    status_code=HTTPStatus.OK,
)
async def list_all(
    service: Service,
    current_user: CurrentUser,
    page_filter: Annotated[FilterPage, Depends(account_filter)] = None,
):
    finance = validate_finance(current_user.finance)
    return await service.list_all_cached(
        page_filter=FilterPage.build(
            page_filter=page_filter, finance_id=str(finance.id)
        ),
        user_request=current_user.username,
    )


@router.get("/{param}", response_model=AccountSchema, status_code=HTTPStatus.OK)
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


@router.post("", response_model=AccountSchema, status_code=HTTPStatus.CREATED)
async def create(
    service: Service, current_user: CurrentUser, payload: PayloadAccountCreateSchema
):
    finance = validate_finance(current_user.finance)
    return await service.persist(finance=finance, payload=payload)


@router.put("/{param}", response_model=AccountSchema, status_code=HTTPStatus.CREATED)
async def update(
    param: str,
    service: Service,
    current_user: CurrentUser,
    payload: PayloadAccountUpdateSchema,
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


@router.post("/list", response_model=list[AccountSchema], status_code=HTTPStatus.OK)
async def create_list(
    service: Service, current_user: CurrentUser, payload: PayloadAccountCreateListSchema
):
    finance = validate_finance(current_user.finance)
    return await service.create_list(finance=finance, payload=payload)

@router.get("/{param}/refresh", response_model=AccountSchema, status_code=HTTPStatus.OK)
async def refresh(
    param: str,
    service: Service,
    current_user: CurrentUser,
):
    finance = validate_finance(current_user.finance)
    return await service.refresh(param=param, finance=finance)