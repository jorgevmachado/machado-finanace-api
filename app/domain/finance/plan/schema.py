from app.domain.finance.account.schema import PayloadAccountCreateSchema
from app.domain.finance.allocation.schema import PayloadAllocationCreateSchema
from app.domain.finance.category.schema import (
    PayloadCategoryCreateSchema,
    CategorySchema,
)
from app.domain.finance.schema import FinanceSchema, PayloadFinanceMonthPersistSchema


class PlanSchema(FinanceSchema):
    categories: list[CategorySchema]


class PayloadPlanChildrenExpenseCreateSchema(PayloadCategoryCreateSchema):
    amount: float
    reference_month: int | None = None


class PayloadPlanExpenseCreateSchema(PayloadFinanceMonthPersistSchema):
    children: list[PayloadPlanChildrenExpenseCreateSchema] | None = []
    reference_month: int | None = None


class PayloadPlanCategoryCreateSchema(PayloadCategoryCreateSchema):
    expenses: list[PayloadPlanExpenseCreateSchema]


class PayloadPlanAllocationCreateSchema(PayloadAllocationCreateSchema):
    categories: list[PayloadPlanCategoryCreateSchema]


class PayloadPlanCreateSchema(PayloadAccountCreateSchema):
    reference_year: int
    allocations: list[PayloadPlanAllocationCreateSchema]
