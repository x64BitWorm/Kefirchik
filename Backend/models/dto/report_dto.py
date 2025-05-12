class ReportOverviewDto:
    def __init__(self, papiks: dict[str, float], debtors: dict[str, float], balances: dict[str, float]):
        self.papiks = papiks
        self.debtors = debtors
        self.balances = balances

class ReportTransactionDto:
    def __init__(self, from_nick: str = '', to_nick: str = '', amount: float = 0.0):
        self.fromNick = from_nick
        self.toNick = to_nick
        self.amount = amount

class ReportInfoDto:
    def __init__(self, transactions_count: int, text: str):
        self.transactions_count = transactions_count
        self.text = text
