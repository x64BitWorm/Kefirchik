class ReportOverviewDto:
    def __init__(self, papiks: dict[str, float], debtors: dict[str, float], balances: dict[str, float], display_names: dict[str, str] = None):
        self.papiks = papiks
        self.debtors = debtors
        self.balances = balances
        self.displayNames = display_names or {}

class ReportTransactionDto:
    def __init__(self, from_nick: str = '', to_nick: str = '', amount: float = 0.0):
        self.fromNick = from_nick
        self.toNick = to_nick
        self.amount = amount

class ReportInfoDto:
    def __init__(self, transactions_count: int, text: str):
        self.transactions_count = transactions_count
        self.text = text


class ReportFileDto:
    def __init__(self, file: bytes, filename: str):
        self.file = file
        self.filename = filename

class MutualBalanceDto:
    def __init__(self, debtor_nick: str = '', papik_nick: str = '', amount: float = 0.0):
        self.debtorNick = debtor_nick
        self.papikNick = papik_nick
        # Строго положительный
        if amount <= 0:
            raise ValueError(f"Amount must be strictly positive, got {amount}")
        self.amount = amount

    def __eq__(self, other):
        if not isinstance(other, MutualBalanceDto):
            return False
        return (
            self.debtorNick == other.debtorNick and
            self.papikNick == other.papikNick and
            self.amount == other.amount
        )
