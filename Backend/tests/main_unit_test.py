from models.dto.report_dto import MutualBalanceDto
from models.db.spending import Spending
from handlers import reports_handler
import unittest

class TestUnits(unittest.IsolatedAsyncioTestCase):
    async def test_mutual_balances(self):
        spendings = [
            newSpending('x64BitWorm', {'Random_Name_0': 500, 'Artem_Barsov': 300}, 800, 'borga'),
            newSpending('Artem_Barsov', {'Random_Name_0': 700}, 800, 'taxi'),
            newSpending('Artem_Barsov', {'x64BitWorm': 200}, 800, 'clubclub'),
        ]
        expected = [
            MutualBalanceDto(debtor_nick='random_name_0', papik_nick='x64bitworm', amount=500),
            MutualBalanceDto(debtor_nick='artem_barsov', papik_nick='x64bitworm', amount=100),
            MutualBalanceDto(debtor_nick='random_name_0', papik_nick='artem_barsov', amount=700),
        ]
        balances = reports_handler.calculateMutualBalances(spendings=spendings)
        self.assertCountEqual(expected, balances)

def newSpending(telegramFromId: str, debtors: dict, costAmount: float, desc: str) -> Spending:
    s = Spending()
    s.telegramFromId = telegramFromId
    s.debtors = debtors
    s.costAmount = costAmount
    s.desc = desc
    s.isCompleted = True
    return s

if __name__ == "__main__":
    unittest.main()
