from enum import Enum

class SpendingType(Enum):
    SIMPLE   = 1,   # Without X's
    RELATIVE = 2,   # With X's

class SpendingMetaInfo:
    def __init__(self, type: SpendingType, remainingAmount: float, xValue: float | None, notFilledUsers: list[str]):
        self.type = type
        self.remainingAmount = remainingAmount
        self.xValue = xValue
        self.notFilledUsers = notFilledUsers
