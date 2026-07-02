from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggingParams
from app.core.service import BaseService
from app.domain.finance.account.schema import PayloadAccountCreateSchema
from app.domain.finance.account.service import AccountService
from app.domain.finance.allocation.schema import PayloadAllocationCreateSchema

from app.domain.finance.allocation.service import AllocationService

from app.domain.finance.allocation_contribution.service import (
    AllocationContributionService,
)
from app.domain.finance.business import merge_months_by_month
from app.domain.finance.category.schema import PayloadCategoryCreateSchema

from app.domain.finance.category.service import CategoryService
from app.domain.finance.expense.schema import PayloadExpenseCreateSchema

from app.domain.finance.expense.service import ExpenseService
from app.domain.finance.expense_month.schema import PayloadExpenseMonthPersistSchema
from app.domain.finance.income.service import IncomeService
from app.domain.finance.plan.schema import (
    PayloadPlanCreateSchema,
)
from app.domain.finance.repository import FinanceRepository
from app.domain.finance.schema import (
    FinanceSchema,
)

from app.models import (
    User,
    Finance,
    Account,
    utcnow,
    MonthStatusEnum,
    CategoryTypeEnum,
)

logger = logging.getLogger(__name__)


class PlanService(BaseService[FinanceRepository, Finance]):
    def __init__(
        self,
        repository: FinanceRepository,
        account_service: AccountService | None = None,
        income_service: IncomeService | None = None,
        allocation_service: AllocationService | None = None,
        category_service: CategoryService | None = None,
        expense_service: ExpenseService | None = None,
        allocation_contribution_service: AllocationContributionService | None = None,
    ) -> None:
        super().__init__(
            alias="Finance",
            repository=repository,
            logger_params=LoggingParams(
                logger=logger, service="FinanceService", operation="finance"
            ),
            schema_class=FinanceSchema,
            cache_prefix="finance",
        )
        session = repository.session
        self.account_service = account_service or AccountService.from_session(session)
        self.income_service = income_service or IncomeService.from_session(session)
        self.allocation_service = allocation_service or AllocationService.from_session(
            session
        )
        self.category_service = category_service or CategoryService.from_session(
            session
        )
        self.expense_service = expense_service or ExpenseService.from_session(session)
        self.allocation_contribution_service = (
            allocation_contribution_service
            or AllocationContributionService.from_session(session)
        )

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(FinanceRepository(session))

    async def onboard(self, current_user: User) -> Finance:
        if current_user.finance:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"User {current_user.username} already onboarded",
            )
        return await self.repository.save(entity=Finance(user_id=current_user.id))

    async def create(
        self, finance: Finance, payloads: list[PayloadPlanCreateSchema]
    ) -> Finance:
        for payload in payloads:
            payload_account_create = PayloadAccountCreateSchema(
                name=payload.name,
                type=payload.type,
                initial_balance=payload.initial_balance or 0,
            )
            account = await self.account_service.persist(
                finance=finance,
                payload=payload_account_create,
                with_throw=False,
            )
            finance.accounts.append(account)
            payload_allocations = payload.allocations or []
            for payload_allocation in payload_allocations:
                payload_allocation_create = PayloadAllocationCreateSchema(
                    name=payload_allocation.name,
                    type=payload_allocation.type,
                    description=payload_allocation.description,
                )
                allocation = await self.allocation_service.persist(
                    finance=finance,
                    payload=payload_allocation_create,
                    with_throw=False,
                )
                finance.allocations.append(allocation)

                payload_categories = payload_allocation.categories or []
                for payload_category in payload_categories:
                    payload_category_create = PayloadCategoryCreateSchema(
                        name=payload_category.name,
                        type=payload_category.type,
                        description=payload_category.description,
                    )
                    category = await self.category_service.persist(
                        finance=finance,
                        payload=payload_category_create,
                        with_throw=False,
                    )
                    finance.categories.append(category)
                    if category.type != CategoryTypeEnum.CREDIT_CARD:
                        merged_payload_expenses = merge_months_by_month(
                            payload_category.expenses or []
                        )
                        if len(merged_payload_expenses) > 0:
                            payload_create_expense_months: list[
                                PayloadExpenseMonthPersistSchema
                            ] = []
                            for (
                                payload_create_expense_month
                            ) in payload_create_expense_months:
                                current_date = utcnow()
                                status = (
                                    MonthStatusEnum.PAID
                                    if current_date.month
                                    > payload_create_expense_month.reference_month
                                    else MonthStatusEnum.PENDING
                                )

                                payload_expense_month_persist = PayloadExpenseMonthPersistSchema(
                                    status=status,
                                    amount=payload_create_expense_month.amount,
                                    reference_month=payload_create_expense_month.reference_month,
                                )
                                payload_create_expense_months.append(
                                    payload_expense_month_persist
                                )

                            payload_create_expense = PayloadExpenseCreateSchema(
                                months=payload_create_expense_months,
                                account_id=account.id,
                                category_id=category.id,
                                allocation_id=allocation.id,
                                description=payload_category.description,
                                reference_year=payload.reference_year,
                            )
                            expense = await self.expense_service.persist(
                                finance=finance,
                                account=account,
                                allocation=allocation,
                                category=category,
                                payload=payload_create_expense,
                                with_throw=False,
                            )
                            finance.expenses.append(expense)
                    else:
                        await self._process_credit_card_category(
                            finance=finance,
                            account=account,
                            allocation=allocation,
                            category=category,
                            payload_category=payload_category,
                            reference_year=payload.reference_year,
                        )

        return finance

    async def _process_credit_card_category(
        self,
        finance: Finance,
        account: Account,
        allocation,
        category,
        payload_category,
        reference_year: int,
    ) -> None:
        """Process CREDIT_CARD category with children expenses."""
        payload_expenses = payload_category.expenses or []

        for payload_expense in payload_expenses:
            # Validar que reference_month está presente
            if not payload_expense.reference_month:
                continue

            # Criar expense pai (CREDIT_CARD)
            current_date = utcnow()
            status = (
                MonthStatusEnum.PAID
                if current_date.month > payload_expense.reference_month
                else MonthStatusEnum.PENDING
            )

            parent_expense_month = PayloadExpenseMonthPersistSchema(
                status=status,
                amount=payload_expense.amount,
                reference_month=payload_expense.reference_month,
            )

            parent_payload_expense = PayloadExpenseCreateSchema(
                months=[parent_expense_month],
                account_id=account.id,
                category_id=category.id,
                allocation_id=allocation.id,
                description=payload_category.description,
                reference_year=reference_year,
            )

            parent_expense = await self.expense_service.persist(
                finance=finance,
                account=account,
                allocation=allocation,
                category=category,
                payload=parent_payload_expense,
                with_throw=False,
            )
            finance.expenses.append(parent_expense)

            # Processar children: agrupar por tipo de categoria e nome
            children_by_type: dict[str, list] = {}
            for child in payload_expense.children or []:
                category_type = (
                    child.type.value
                    if hasattr(child.type, "value")
                    else str(child.type)
                )
                if category_type not in children_by_type:
                    children_by_type[category_type] = []
                children_by_type[category_type].append(child)

            # Para cada tipo de categoria, agrupar children e mesclar por month
            for category_type_key, children_list in children_by_type.items():
                # Mesclar months dos children com mesmo reference_month
                merged_children = self._merge_children_by_month(children_list)

                # Criar categoria para o child com o tipo específico
                child_category_create = PayloadCategoryCreateSchema(
                    name=f"Credit Card - {children_list[0].type}",
                    type=children_list[0].type,
                    description=f"Children expenses of {category.name}",
                )

                child_category = await self.category_service.persist(
                    finance=finance,
                    payload=child_category_create,
                    with_throw=False,
                )
                finance.categories.append(child_category)

                # Criar expense para cada merged child
                for merged_child in merged_children:
                    reference_month = merged_child.get("reference_month")
                    if reference_month is None:
                        continue

                    current_date = utcnow()
                    status = (
                        MonthStatusEnum.PAID
                        if current_date.month > reference_month
                        else MonthStatusEnum.PENDING
                    )

                    child_expense_month = PayloadExpenseMonthPersistSchema(
                        status=status,
                        amount=merged_child.get("amount", 0),
                        reference_month=reference_month,
                    )

                    child_payload_expense = PayloadExpenseCreateSchema(
                        months=[child_expense_month],
                        account_id=account.id,
                        category_id=child_category.id,
                        allocation_id=allocation.id,
                        description=merged_child.get("name", ""),
                        reference_year=reference_year,
                        parent_id=parent_expense.id,
                    )

                    child_expense = await self.expense_service.persist(
                        finance=finance,
                        account=account,
                        allocation=allocation,
                        category=child_category,
                        payload=child_payload_expense,
                        with_throw=False,
                    )
                    finance.expenses.append(child_expense)

    def _merge_children_by_month(self, children: list) -> list[dict]:
        """Merge children expenses by reference_month, summing amounts."""
        merged: dict[int, dict] = {}

        for child in children:
            reference_month = (
                child.reference_month if hasattr(child, "reference_month") else None
            )
            if reference_month is None:
                reference_month = (
                    child.get("reference_month") if isinstance(child, dict) else None
                )

            if reference_month is None:
                continue

            if reference_month not in merged:
                child_name = (
                    child.name
                    if hasattr(child, "name")
                    else child.get("name", "Unknown")
                )
                merged[reference_month] = {
                    "reference_month": reference_month,
                    "amount": child.amount
                    if hasattr(child, "amount")
                    else child.get("amount", 0),
                    "name": child_name,
                }
            else:
                child_amount = (
                    child.amount if hasattr(child, "amount") else child.get("amount", 0)
                )
                merged[reference_month]["amount"] += child_amount

        return list(merged.values())
