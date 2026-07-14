from app.domain.finance.category.schema import PayloadCategoryCreateSchema

DEFAULT_CATEGORIES: list[PayloadCategoryCreateSchema] = [
    PayloadCategoryCreateSchema(
        name="Others",
        description="Miscellaneous expenses that do not fit into other categories."
    ),
    PayloadCategoryCreateSchema(
        name="House",
        description="Expenses related to housing, including rent, mortgage, utilities, and maintenance."
    ),
    PayloadCategoryCreateSchema(
        name="Transportation",
        description="Costs associated with commuting, public transportation, fuel, and vehicle maintenance."
    ),
    PayloadCategoryCreateSchema(
        name="Food",
        description="Expenses for groceries, dining out, and other food-related costs."
    ),
    PayloadCategoryCreateSchema(
        name="Clothing",
        description="Spending on apparel, shoes, and accessories."
    ),
    PayloadCategoryCreateSchema(
        name="Entertainment",
        description="Spending on leisure activities, hobbies, movies, concerts, and other forms of entertainment."
    ),
    PayloadCategoryCreateSchema(
        name="Healthcare",
        description="Medical expenses, including insurance premiums, doctor visits, medications, and treatments."
    ),
    PayloadCategoryCreateSchema(
        name="Education",
        description="Costs related to tuition, books, courses, and other educational expenses."
    ),
    PayloadCategoryCreateSchema(
        name="Savings & Investments",
        description="Funds allocated for savings accounts, retirement plans, stocks, bonds, and other investment vehicles."
    ),
    PayloadCategoryCreateSchema(
        name="Public Taxes",
        description="Mandatory payments to government authorities, including income tax, property tax, and other levies."
    ),
    PayloadCategoryCreateSchema(
        name="Services",
        description="Payments for professional services, subscriptions, and other service-related expenses."
    )
]