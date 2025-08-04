from models.dto.spendings_dto import SpendingMetaInfo
from utils import BotException, BotWrongInputException
from models.db.spending import Spending
import services.calculations as calculations
from services.parsers import ParsedQuery

def isSpendingCompleted(debtors: any):
    notFilledUsers = getUnfilledUsers(debtors)
    return len(notFilledUsers) == 0

def getReplyText(data: ParsedQuery):
    notFilledUsers = getUnfilledUsers(data.debtors)
    text = 'Запомнил🍶'
    if len(notFilledUsers) > 0:
        text += f' ждем {" @".join([""] + notFilledUsers)}'
    return text

def getUnfilledUsers(debtors):
    names = []
    for k, v in debtors.items():
        if not v:
            names.append(k)
    return names

def getDebtorsWithAmounts(debtors, amount):
    ans = calculations.calculate_spendings(debtors.values(), amount)
    for i, (k, v) in enumerate(debtors.items()):
        debtors[k] = ans[i]
    return debtors

def getSpendingMetaInfo(spending: Spending) -> SpendingMetaInfo:
    notFilledUsers = getUnfilledUsers(spending.debtors)
    expressions = list(filter(lambda x: x != '', spending.debtors.values()))
    spendingType, remainingAmount = calculations.get_spending_meta_info(expressions, spending.costAmount)
    return SpendingMetaInfo(type=spendingType, remainingAmount=remainingAmount, notFilledUsers=notFilledUsers)

def getExpressionOfReply(text: str, user: str, spending: Spending) -> str:
    expression = text
    if len(expression) > 100:
        raise BotException('🤓☝️ Внатуре задрот')
    if expression.startswith('...'):
        if len(spending.debtors[user]) == 0:
            raise BotWrongInputException()
        expression = spending.debtors[user] + expression[3:]
    answer = calculations.parse_expression(expression)
    if answer[0] < 0 or answer[0] > spending.costAmount:
        raise BotWrongInputException()
    return expression

def getUsersFromSpendings(spendings: list[Spending]) -> str:
    users = {spending.telegramFromId for spending in spendings}
    return "@" + " @".join(sorted(users)) if users else ""
