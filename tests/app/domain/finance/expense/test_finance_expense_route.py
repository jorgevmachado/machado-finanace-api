from uuid import uuid4

from app.domain.finance.expense.route import expense_filter
from app.shared.schemas import FilterPage


class TestExpenseFilter:
    def test_expense_filter_with_all_defaults(self):
        result = expense_filter()
        assert isinstance(result, FilterPage)
        assert result.limit == 12
        assert result.page is None
        assert result.offset is None
        assert result.clean_cache is False
        assert result.with_deleted is False

    def test_expense_filter_with_custom_page(self):
        result = expense_filter(page=2)
        assert result.page == 2

    def test_expense_filter_with_custom_limit(self):
        result = expense_filter(limit=50)
        assert result.limit == 50

    def test_expense_filter_with_custom_status(self):
        result = expense_filter(status="PAID")
        assert result.status == "PAID"

    def test_expense_filter_with_custom_offset(self):
        result = expense_filter(offset=10)
        assert result.offset == 10

    def test_expense_filter_with_account_id(self):
        account_id = str(uuid4())
        result = expense_filter(account_id=account_id)
        assert result.account_id == account_id

    def test_expense_filter_with_category_id(self):
        category_id = str(uuid4())
        result = expense_filter(category_id=category_id)
        assert result.category_id == category_id

    def test_expense_filter_with_allocation_id(self):
        allocation_id = str(uuid4())
        result = expense_filter(allocation_id=allocation_id)
        assert result.allocation_id == allocation_id

    def test_expense_filter_with_clean_cache(self):
        result = expense_filter(clean_cache=True)
        assert result.clean_cache is True

    def test_expense_filter_with_deleted(self):
        result = expense_filter(with_deleted=True)
        assert result.with_deleted is True

    def test_expense_filter_with_all_parameters(self):
        account_id = str(uuid4())
        category_id = str(uuid4())
        allocation_id = str(uuid4())

        result = expense_filter(
            page=1,
            limit=20,
            status="PENDING",
            offset=0,
            account_id=account_id,
            category_id=category_id,
            allocation_id=allocation_id,
            clean_cache=True,
            with_deleted=True,
        )

        assert result.page == 1
        assert result.limit == 20
        assert result.status == "PENDING"
        assert result.offset == 0
        assert result.account_id == account_id
        assert result.category_id == category_id
        assert result.allocation_id == allocation_id
        assert result.clean_cache is True
        assert result.with_deleted is True
