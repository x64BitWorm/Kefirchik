from enum import Enum

class SpendingType(Enum):
    # Without X's
    SIMPLE = 1,
    # With X's
    RELATIVE = 2,

class SpendingMetaInfo:
    def __init__(self, type: SpendingType, remainingAmount: float, notFilledUsers: list[str]):
        self.type = type
        self.remainingAmount = remainingAmount
        self.notFilledUsers = notFilledUsers
