from enum import Enum


class StatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class RoleEnum(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class AccountTypeEnum(str, Enum):
    PIX = "PIX"
    BANK = "BANK"
    CASH = "CASH"
    OTHER = "OTHER"
    INVESTMENT = "INVESTMENT"
    CREDIT_CARD = "CREDIT_CARD"
    ACCOUNT_DEBIT = "ACCOUNT_DEBIT"


class AllocationTypeEnum(str, Enum):
    OTHER = "OTHER"
    HOUSE = "HOUSE"
    FAMILY = "FAMILY"
    PERSONAL = "PERSONAL"


class CategoryTypeEnum(str, Enum):
    FOOD = "FOOD"
    OTHER = "OTHER"
    STUDIES = "STUDIES"
    UTILITY = "UTILITY"
    HEALTH = "HEALTH"
    PERSONAL = "PERSONAL"
    TRANSPORT = "TRANSPORT"
    ENTERTAINMENT = ("ENTERTAINMENT",)
    GOVERNMENT_FEES = "GOVERNMENT_FEES"


class MonthStatusEnum(str, Enum):
    PAID = "PAID"
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"
