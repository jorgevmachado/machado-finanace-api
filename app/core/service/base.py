from http import HTTPStatus
from typing import Annotated, cast

from fastapi import HTTPException, Query
from pydantic import BaseModel

from app.core.cache.service import CacheService
from app.core.exceptions import handle_service_exception
from app.core.logging import LoggingParams, log_service_success
from app.core.pagination.pagination import exception_pagination
from app.models import utcnow
from app.shared.schemas import FilterPage, Message
from app.shared.utils.string import is_valid_uuid


class BaseService[
    RepositoryT,
    ModelT,
    SchemaT: BaseModel = BaseModel,
    UpdateSchemaT: BaseModel = BaseModel,
]:
    def __init__(
        self,
        alias: str,
        repository: RepositoryT,
        logger_params: LoggingParams,
        schema_class: type[SchemaT],
        cache_prefix: str | None = None,
    ):
        prefix = cache_prefix or alias.replace(" ", "_").lower()
        self.alias = alias
        self.repository = repository
        self.cache_prefix = cache_prefix
        self.logger_params = logger_params
        self.cache_service = CacheService(
            alias=alias,
            prefix=prefix,
            logger_params=logger_params,
            schema_class=schema_class,
        )

    async def list_all(
        self,
        page_filter: Annotated[FilterPage, Query()] = None,
        user_request: str | None = None,
    ):
        try:
            return await self.repository.list_all(page_filter=page_filter)
        except Exception as exception:
            handle_service_exception(
                exception,
                logger=self.logger_params.logger,
                service=self.logger_params.service,
                operation="list_all",
                user_request=user_request,
                raise_exception=False,
            )
            return exception_pagination(page_filter)
        finally:
            log_service_success(
                self.logger_params,
                operation="list_all",
                message="List all successfully",
                user_request=user_request,
            )

    async def list_all_cached(
        self,
        page_filter: Annotated[FilterPage, Query()] = None,
        user_request: str | None = None,
        **kwargs,
    ):
        clean_cache = page_filter.clean_cache if page_filter else False
        if clean_cache:
            await self.cache_service.delete_domain()
        if page_filter:
            page_filter.clean_cache = None
        key = self.cache_service.build_key_list(page_filter=page_filter)
        cached = await self.cache_service.get_list(key)
        if cached:
            return cached
        result = await self.list_all(page_filter=page_filter, user_request=user_request)

        await self.cache_service.set_list(key, result)

        return result

    async def find_one(
        self,
        param: str,
        **kwargs,
    ):
        finance_id = kwargs.get("finance_id") if kwargs else None
        user_request = kwargs.get("user_request") if kwargs else None
        with_deleted = kwargs.get("with_deleted") if kwargs else False
        finance_id = cast(str, finance_id) if finance_id else None
        try:
            find_by_filters: dict[str, str] = (
                {"finance_id": finance_id} if finance_id else {}
            )
            if is_valid_uuid(param):
                result = await self.repository.find_by(id=param, with_deleted=with_deleted, **find_by_filters)
            else:
                result = await self.repository.find_by(name=param, with_deleted=with_deleted, **find_by_filters)

            if result is None:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"{self.alias} not found",
                )
            return result
        except Exception as exception:
            handle_service_exception(
                exception,
                logger=self.logger_params.logger,
                service=self.logger_params.service,
                operation="find_one",
                user_request=user_request,
                raise_exception=True,
            )
        finally:
            log_service_success(
                self.logger_params,
                operation="find_one",
                message=f"Find one {self.alias} successfully",
                user_request=user_request,
            )

    async def _invalidate_cache(
        self, identifier: str | None = None, finance_id: str | None = None
    ) -> None:
        await self.cache_service.delete_domain()
        if identifier:
            cache_key = identifier
            if finance_id:
                cache_key = f"{finance_id}:{identifier}"
            await self.cache_service.cache.delete_cache(cache_key)

    async def find_one_cached(
        self,
        param: str,
        **kwargs,
    ):
        cache_key = param
        finance_id = kwargs.get("finance_id") if kwargs else None
        finance_id = cast(str, finance_id) if finance_id else None
        if finance_id:
            cache_key = f"{finance_id}:{param}"
        key = self.cache_service.build_key_one(param=cache_key)
        clean_cache = kwargs.get("clean_cache") if kwargs else False

        if clean_cache:
            await self.cache_service.cache.delete_cache(key)
        cached = await self.cache_service.get_one(key)
        if cached:
            return cached
        item = await self.find_one(param, **kwargs)
        await self.cache_service.set_one(key, item)
        return item

    async def find_by(self, **kwargs):
        user_request = kwargs.get("user_request", None)
        without_throw = kwargs.get("without_throw", False)
        kwargs.pop("without_throw", None)
        try:
            result = await self.repository.find_by(**kwargs)
            if result is None and not without_throw:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"{self.alias} not found",
                )
            return result
        except Exception as exception:
            handle_service_exception(
                exception,
                logger=self.logger_params.logger,
                service=self.logger_params.service,
                operation="find_by",
                user_request=user_request,
            )
        finally:
            log_service_success(
                self.logger_params,
                operation="find_by",
                message=f"Find by {self.alias} successfully",
                user_request=user_request,
            )

    async def update(
        self,
        param: str,
        update_schema: UpdateSchemaT,
        **kwargs
    ) -> ModelT:
        user_request = kwargs.get("user_request", None)
        finance_id = kwargs.get("finance_id") if kwargs else None
        finance_id = cast(str, finance_id) if finance_id else None
        kwargs.pop("finance_id", None)
        try:
            entity = await self.find_one(param, user_request=user_request)
            if entity is None:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"{self.alias} not found",
                )
            update_data = update_schema.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                if isinstance(entity, dict):
                    entity[key] = value
                else:
                    setattr(entity, key, value)
            await self._invalidate_cache(identifier=param, finance_id=finance_id)
            return await self.repository.update(entity)
        except Exception as exception:
            handle_service_exception(
                exception,
                logger=self.logger_params.logger,
                service=self.logger_params.service,
                operation="update",
                user_request=user_request,
                raise_exception=True,
            )
        finally:
            log_service_success(
                self.logger_params,
                operation="update",
                message=f"Update {self.alias} successfully",
                user_request=user_request,
            )

    async def update_entity(
        self,
        entity: ModelT,
        user_request: str | None = None,
    ) -> ModelT:
        try:
            return await self.repository.update(entity=entity)
        except Exception as exception:
            handle_service_exception(
                exception,
                logger=self.logger_params.logger,
                service=self.logger_params.service,
                operation="update",
                user_request=user_request,
                raise_exception=True,
            )
        finally:
            log_service_success(
                self.logger_params,
                operation="update",
                message=f"Update Entity {self.alias} successfully",
                user_request=user_request,
            )

    async def soft_delete(
            self,
            param: str,
            **kwargs
    ) -> Message:
        user_request = kwargs.get("user_request") if kwargs else None
        finance_id = kwargs.get("finance_id") if kwargs else None
        finance_id = cast(str, finance_id) if finance_id else None
        kwargs.pop("finance_id", None)
        successfully_message = f"Deleted {self.alias} successfully"
        try:
            entity = await self.find_one(param=param, finance_id=finance_id, **kwargs)
            if entity is None:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"{self.alias} not found",
                )
            await self._invalidate_cache(identifier=param, finance_id=finance_id)
            entity.deleted_at = utcnow()
            await self.repository.update(entity)
            return Message(message=successfully_message)
        except Exception as exception:
            handle_service_exception(
                exception,
                logger=self.logger_params.logger,
                service=self.logger_params.service,
                operation="soft_delete",
                user_request=user_request,
                raise_exception=True,
            )
        finally:
            log_service_success(
                self.logger_params,
                operation="soft_delete",
                message=successfully_message,
                user_request=user_request,
            )