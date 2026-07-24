from __future__ import annotations

from datetime import date
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.pagination import CustomLimitOffsetPage
from app.core.security import get_current_user
from app.core.security.security import validate_finance

from app.domain.finance.transfer.repository import TransferRepository
from app.domain.finance.transfer.schema import (
    TransferSchema,
    PayloadTransferCreateSchema,
    PayloadTransferUpdateSchema,
)
from app.domain.finance.transfer.service import TransferService
from app.models import User
from app.shared.schemas import FilterPage, Message

router = APIRouter()

Session = Annotated[AsyncSession, Depends(get_session)]


def transfer_service(session: Session) -> TransferService:
    return TransferService(TransferRepository(session))


Service = Annotated[TransferService, Depends(transfer_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def transfer_filter(
    page: int | None = None,
    limit: int | None = 12,
    offset: int | None = None,
    transfer_date: date | None = None,
    to_account_id: str | None = None,
    from_account_id: str | None = None,
    clean_cache: bool = False,
    with_deleted: bool = False,
) -> FilterPage:
    return FilterPage.build(
        page=page,
        limit=limit,
        offset=offset,
        transfer_date=transfer_date,
        to_account_id=to_account_id,
        from_account_id=from_account_id,
        clean_cache=clean_cache,
        with_deleted=with_deleted,
    )


@router.get(
    "",
    response_model=CustomLimitOffsetPage[TransferSchema] | list[TransferSchema],
    status_code=HTTPStatus.OK,
)
async def list_all(
    service: Service,
    current_user: CurrentUser,
    page_filter: Annotated[FilterPage, Depends(transfer_filter)] = None,
):
    finance = validate_finance(current_user.finance)
    return await service.list_all_cached(
        page_filter=FilterPage.build(
            page_filter=page_filter, finance_id=str(finance.id)
        ),
        user_request=current_user.username,
    )


@router.get("/{param}", response_model=TransferSchema, status_code=HTTPStatus.OK)
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


@router.post("", response_model=TransferSchema, status_code=HTTPStatus.CREATED)
async def create(
    service: Service, current_user: CurrentUser, payload: PayloadTransferCreateSchema
):
    finance = validate_finance(current_user.finance)
    return await service.create(finance=finance, payload=payload)


@router.put("/{param}", response_model=TransferSchema, status_code=HTTPStatus.CREATED)
async def update(
    param: str,
    service: Service,
    current_user: CurrentUser,
    payload: PayloadTransferUpdateSchema,
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
