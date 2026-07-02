from __future__ import annotations

from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.pagination import CustomLimitOffsetPage
from app.core.security import get_current_user
from app.core.security.security import validate_finance

from app.domain.finance.expense.repository import ExpenseRepository
from app.domain.finance.expense.schema import (
    ExpenseSchema,
    PayloadExpenseCreateSchema,
    PayloadExpenseUpdateSchema,
)
from app.domain.finance.expense.service import ExpenseService
from app.models import User
from app.shared.schemas import FilterPage, Message

router = APIRouter()

Session = Annotated[AsyncSession, Depends(get_session)]


def expense_service(session: Session) -> ExpenseService:
    return ExpenseService(ExpenseRepository(session))


Service = Annotated[ExpenseService, Depends(expense_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def expense_filter(
    page: int | None = None,
    limit: int | None = 12,
    status: str | None = None,
    offset: int | None = None,
    account_id: str | None = None,
    category_id: str | None = None,
    allocation_id: str | None = None,
    clean_cache: bool = False,
    with_deleted: bool = False,
) -> FilterPage:
    return FilterPage.build(
        page=page,
        limit=limit,
        status=status,
        offset=offset,
        account_id=account_id,
        category_id=category_id,
        allocation_id=allocation_id,
        clean_cache=clean_cache,
        with_deleted=with_deleted,
    )


@router.get(
    "",
    response_model=CustomLimitOffsetPage[ExpenseSchema] | list[ExpenseSchema],
    status_code=HTTPStatus.OK,
)
async def list_all(
    service: Service,
    current_user: CurrentUser,
    page_filter: Annotated[FilterPage, Depends(expense_filter)] = None,
):
    finance = validate_finance(current_user.finance)
    return await service.list_all_cached(
        page_filter=FilterPage.build(
            page_filter=page_filter, finance_id=str(finance.id)
        ),
        user_request=current_user.username,
    )


@router.get("/{param}", response_model=ExpenseSchema, status_code=HTTPStatus.OK)
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


@router.post("", response_model=ExpenseSchema, status_code=HTTPStatus.CREATED)
async def create(
    service: Service, current_user: CurrentUser, payload: PayloadExpenseCreateSchema
):
    finance = validate_finance(current_user.finance)
    return await service.create(finance=finance, payload=payload)


@router.put("/{param}", response_model=ExpenseSchema, status_code=HTTPStatus.CREATED)
async def update(
    param: str,
    service: Service,
    current_user: CurrentUser,
    payload: PayloadExpenseUpdateSchema,
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
