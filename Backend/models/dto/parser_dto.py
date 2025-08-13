class ParsedSpendingBody:
    def __init__(self, debtors: dict[str, str], comment: str):
        self.debtors = debtors
        self.comment = comment