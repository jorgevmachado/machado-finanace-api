from __future__ import annotations

import logging
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService

from app.domain.finance.allocation.service import AllocationService
from app.domain.finance.category.schema import CategorySchema

from app.domain.finance.category.service import CategoryService
from app.domain.finance.expense.business import parse_pdf, generate_months_by_year

from app.domain.finance.expense.repository import (
    ExpenseRepository,
)
from app.domain.finance.expense.schema import (
    ExpenseSchema,
    PayloadExpenseCreateSchema,
    PayloadExpenseUpdateSchema,
    UploadedResultSchema,
    UploadedExpenseResultSchema, PayloadExpenseListPersist,
)
from app.domain.finance.expense_month.service import ExpenseMonthService
from app.domain.finance.months.business import merge_months_by_month
from app.domain.finance.months.schema import PayloadMonthPersistSchema

from app.models import (
    Expense,
    Finance,
    Allocation,
    Category,
    utcnow,
    BankEnum,
)
from app.shared.utils.string import to_snake_case
from app.shared.utils.validator import validate_year

logger = logging.getLogger(__name__)


class ExpenseService(BaseService[ExpenseRepository, Expense]):
    def __init__(
        self,
        repository: ExpenseRepository,
        category_service: CategoryService | None = None,
        allocation_service: AllocationService | None = None,
        expense_month_service: ExpenseMonthService | None = None,
    ) -> None:
        super().__init__(
            alias="Expense",
            repository=repository,
            logger_params=LoggingParams(
                logger=logger,
                service="ExpenseService",
                operation="expense",
            ),
            schema_class=ExpenseSchema,
            cache_prefix="expense",
        )
        session = repository.session
        self.category_service = category_service or CategoryService.from_session(
            session
        )
        self.allocation_service = allocation_service or AllocationService.from_session(
            session
        )
        self.expense_month_service = (
            expense_month_service or ExpenseMonthService.from_session(session)
        )

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(ExpenseRepository(session))

    async def update(self, param: str, payload: PayloadExpenseUpdateSchema, **kwargs) -> Expense:
        reference_year = payload.reference_year if payload.reference_year else utcnow().year
        entity = await self.find_one(param=param)
        has_change = False
        
        allocation = entity.allocation
        if payload.allocation_id and payload.allocation_id != entity.allocation_id:
            allocation = await self.allocation_service.find_by(
                id=payload.allocation_id, without_throw=True
            )
            if not allocation:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Allocation with this id {payload.allocation_id} does not exist",
                )
            entity.allocation_id = allocation.id
            has_change = True
        
        category = entity.category
        if payload.category_id and payload.category_id != entity.category_id:
            category = await self.category_service.find_by(
                id=payload.category_id,
                finance_id=entity.category.finance_id,
                without_throw=True,
            )
            if not category:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Category {payload.category_id} not found",
                )
            entity.category_id = category
            has_change = True
        
        if payload.payee and payload.payee != entity.payee: 
            payee_code = to_snake_case(payload.payee or '')
            existing_expense = await self.find_by(
                payee_code=payee_code,
                category_id=category.id,
                allocation_id=allocation.id,
                without_throw=True,
            )
            if existing_expense and existing_expense.id != entity.id:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Expense with payee {payload.payee} already exists",
                )
            entity.payee = payload.payee
            entity.payee_code = payee_code
            has_change = True
            
        if payload.description and payload.description != entity.description: 
            entity.description = payload.description
            has_change = True
        
        if payload.parent_id and payload.parent_id != entity.parent_id:
            parent = await self.find_by(id=payload.parent_id, without_throw=True)
            if not parent:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Parent expense with id {payload.parent_id} does not exist",
                )
            entity.parent_id = payload.parent_id
            has_change = True
        
        if payload.months and payload.months != entity.months:
            payload_months = [
                PayloadMonthPersistSchema(
                    amount=month.amount,
                    status=month.status,
                    reference_day=payload.reference_day or 10,
                    reference_month=month.reference_month,
                    transaction_date=month.transaction_date,
                )
                for month in payload.months or []
            ]
            await self.expense_month_service.persist_list(
                expense=entity,
                months=payload_months,
                reference_day=payload.reference_day or 10,
                reference_year=reference_year,
            )
            has_change = True

        if not has_change:
            return entity
        await self.cache_service.delete_domain()
        return await self.repository.update(entity=entity)
        
    async def create(
        self, finance: Finance, payload: PayloadExpenseCreateSchema, with_throw: bool = True,
    ) -> Expense:

        allocation = await self.allocation_service.find_by(
            id=payload.allocation_id, without_throw=True
        )
        if not allocation:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Allocation with this id {payload.allocation_id} does not exist",
            )

        category = await self.category_service.find_by(
            id=payload.category_id,
            finance_id=finance.id,
            without_throw=True,
        )

        if not category:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Category {payload.category_id} not found for finance {finance.id}",
            )

        return await self.persist(
            payee=payload.payee,
            months=payload.months,
            category=category,
            parent_id=payload.parent_id,
            allocation=allocation,
            with_throw=with_throw,
            description=payload.description,
            reference_day=payload.reference_day or 10,
            reference_year=payload.reference_year,
        )

    async def persist(
        self,
        payee: str,
        months: list[PayloadMonthPersistSchema],
        category: Category,
        allocation: Allocation,
        description: str,
        reference_day: int,
        reference_year: int,
        parent_id: UUID | None = None,
        with_throw: bool = True,
    ) -> Expense:

        year = validate_year(reference_year)

        payee_code = to_snake_case(payee)

        expense = await self.find_by(
            payee_code=payee_code,
            category_id=category.id,
            description=description,
            allocation_id=allocation.id,
            without_throw=True,
        )
        if expense:
            if with_throw:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Expense with payee {payee} already exists",
                )
            else:
                expense.description = description
                expense.parent_id = parent_id
                persisted_months = [
                    PayloadMonthPersistSchema(
                        amount=float(month.amount),
                        status=month.status,
                        reference_month=month.reference_month,
                        transaction_date=month.paid_at.date() if month.paid_at else None,
                        reference_day=reference_day,
                    )
                    for month in (expense.months or [])
                ]
                merged_months = merge_months_by_month([*persisted_months, *months])
                await self.expense_month_service.persist_list(
                    months=merged_months,
                    expense=expense,
                    reference_year=year,
                    reference_day=reference_day,
                )
                return await self.repository.update(entity=expense)

        else:
            created_expense = await self.repository.save(
                entity=Expense(
                    payee=payee,
                    parent_id=parent_id,
                    payee_code=payee_code,
                    category_id=category.id,
                    description=description,
                    allocation_id=allocation.id,
                )
            )
            saved_months = await self.expense_month_service.persist_list(
                months=months,
                expense=created_expense,
                reference_day=reference_day,
                reference_year=year,
            )

            saved_expense = await self.find_by(id=created_expense.id)
            saved_expense.months = saved_months
            return saved_expense

    async def upload(
            self,
            file: UploadFile,
            bank: BankEnum,
            finance: Finance,
            allocation_id: str,
            reference_year: int | None = None,
            reference_month: int | None = None
    ) -> UploadedResultSchema:
        allocation = await self.allocation_service.find_by(
            id=allocation_id, without_throw=True
        )
        if not allocation:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Allocation with this id {allocation_id} does not exist",
            )
        if file.content_type != 'application/pdf':
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="File must be a PDF",
            )

        contents = await file.read()

        parsed = parse_pdf(
            file=contents,
            bank=bank,
            allocation=allocation,
            reference_year=reference_year,
            reference_month=reference_month,
        )

        if parsed.error:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=parsed.message,
            )
        parent_category: CategorySchema = await self.upload_validate_category(finance, category_name="Credit Card")
        uploaded_expenses_result: list[UploadedExpenseResultSchema] = []
        for parsed_expense in parsed.expenses:
            parsed_expense_payee_code = to_snake_case(parsed_expense.payee)
            exist_expense = await self.find_by(payee_code=parsed_expense_payee_code, without_throw=True)
            category_name = parsed_expense.category
            category = exist_expense.category if exist_expense else None
            category_schema = await self.upload_validate_category(finance, category, category_name)
            uploaded_expenses_result.append(UploadedExpenseResultSchema(
                date=parsed_expense.date,
                payee=parsed_expense.payee,
                amount=parsed_expense.amount,
                category=category_schema,
                reference_month=parsed_expense.reference_month,
                current_installment=parsed_expense.current_installment,
                total_of_installments=parsed_expense.total_of_installments
            ))
        return UploadedResultSchema(
            bank=parsed.bank,
            error=parsed.error,
            message=parsed.message,
            category=parent_category,
            expenses=uploaded_expenses_result,
            allocation=parsed.allocation,
            bill_total=parsed.bill_total,
            bill_due_date=parsed.bill_due_date,
            date_of_issue=parsed.date_of_issue,
            reference_year=parsed.reference_year,
            reference_month=parsed.reference_month,
            previous_bill_total=parsed.previous_bill_total,
            previous_bill_due_date=parsed.previous_bill_due_date
        )

    async def upload_validate_category(self, finance: Finance, category: Category | None = None, category_name: str | None = None) -> CategorySchema:
        if category:
            return CategorySchema.model_validate(category)
        category_name = category_name if category_name else "OTHERS"
        description = f"Category {category_name} generated from file upload" if category_name else "Default category for expenses without a specific category"
        category = await self.category_service.persist(
            name=category_name,
            finance=finance,
            description=description,
            with_throw=False,
        )
        return CategorySchema.model_validate(category)
    
    async def persist_list(self, finance: Finance, payload: PayloadExpenseListPersist) -> list[Expense]:
        parent_expense = None
        reference_year = utcnow().year
        reference_day = 10
        if payload.parent:
            reference_year = (
                payload.parent.reference_year
                if payload.parent.reference_year
                else reference_year
            )
            reference_day = (
                payload.parent.reference_day
                if payload.parent.reference_day
                else reference_day
            )
            parent_expense = await self.create(finance=finance, payload=payload.parent, with_throw=False)
        expenses = []
        for expense_payload in payload.expenses:
            if parent_expense:
                expense_payload.parent_id = parent_expense.id
            expense = await self.create(finance=finance, payload=expense_payload, with_throw=False)
            expenses.append(expense)
        if parent_expense:
            months_by_year = generate_months_by_year(expenses)
            for year, months in months_by_year.items():
                await self.expense_month_service.persist_list(
                    months=months,
                    expense=parent_expense,
                    reference_year=year,
                    reference_day=reference_day
                )
            parent_expense = await self.repository.update(entity=parent_expense)    
            parent_expense.children = expenses
            return [parent_expense]
        return expenses