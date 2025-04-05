class ReportOverviewDto:
    def __init__(self):
        self.papiks: dict[str, float] = {}
        self.debtors: dict[str, float] = {}
        self.balances: dict[str, float] = {}

class ReportTransactionDto:
    def __init__(self, from_nick: str = '', to_nick: str = '', amount: float = 0.0):
        self.fromNick = from_nick
        self.toNick = to_nick
        self.amount = amount

class ReportInfoDto:
    def __init__(self, transactions: int, text: str):
        self.transactions = transactions
        self.text = text
