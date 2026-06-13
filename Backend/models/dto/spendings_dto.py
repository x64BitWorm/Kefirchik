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

class SpendingCompletionResult:
    def __init__(self, completed: bool, debtors: dict, error: str | None = None):
        self.completed = completed
        self.debtors = debtors
        self.error = error
