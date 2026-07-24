from pydantic import BaseModel
from datetime import date

from app.domain.finance.allocation.schema import AllocationSchema
from app.models import BankEnum

class ParsedPDFExpenseSchema(BaseModel):
    date: date
    payee: str
    amount: float
    category: str
    reference_month: int    
    current_installment: int
    all_installments_paid: bool
    total_of_installments: int

class ParsedPDFSchema(BaseModel):
    bank: BankEnum
    error: bool
    message: str
    expenses: list[ParsedPDFExpenseSchema]
    allocation: AllocationSchema
    bill_total: float
    bill_due_date: date | None = None
    date_of_issue: date | None = None
    reference_year: int
    reference_month: int
    previous_bill_total: float
    previous_bill_due_date: date | None = None
