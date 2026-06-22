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
