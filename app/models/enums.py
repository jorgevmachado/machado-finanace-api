from enum import Enum


class StatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class RoleEnum(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class AccountTypeEnum(str, Enum):
    BANK = "BANK"
    CASH = "CASH"
    OTHER = "OTHER"
    INVESTMENT = "INVESTMENT"


class CategoryTypeEnum(str, Enum):
    FOOD = "FOOD"
    OTHER = "OTHER"
    STUDIES = "STUDIES"
    UTILITY = "UTILITY"
    HEALTH = "HEALTH"
    PERSONAL = "PERSONAL"
    TRANSPORT = "TRANSPORT"
    CREDIT_CARD = "CREDIT_CARD"
    ENTERTAINMENT = "ENTERTAINMENT"
    GOVERNMENT_FEES = "GOVERNMENT_FEES"


class MonthStatusEnum(str, Enum):
    PAID = "PAID"
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"

class BankEnum(str, Enum):
    ITAU = "ITAU"
    CAIXA = "CAIXA"
    NUBANK = "NUBANK"