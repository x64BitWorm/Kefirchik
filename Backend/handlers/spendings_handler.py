from models.dto.spendings_dto import SpendingCompletionResult, SpendingMetaInfo
import utils
from utils import BotException, BotWrongInputException
from models.db.spending import Spending
import services.calculations as calculations
from handlers import parsers_handler

def isSpendingCompleted(debtors: any):
    notFilledUsers = getUnfilledUsers(debtors)
    return len(notFilledUsers) == 0

def getReplyText(data: parsers_handler.ParsedQuery):
    notFilledUsers = getUnfilledUsers(data.debtors)
    text = 'Запомнил🍶'
    if len(notFilledUsers) > 0:
        text += f' ждем {" @".join([""] + notFilledUsers)}'
    return text

def getUnfilledUsers(debtors: dict[str, str]) -> list[str]:
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

# При расхождении сохраняем введенные доли, но не закрываем трату
def tryCompleteSpending(debtors, amount) -> SpendingCompletionResult:
    if not isSpendingCompleted(debtors):
        return SpendingCompletionResult(False, debtors)
    try:
        return SpendingCompletionResult(True, getDebtorsWithAmounts(debtors, amount))
    except BotException as error:
        return SpendingCompletionResult(False, debtors, str(error))

def getSpendingMetaInfo(spending: Spending) -> SpendingMetaInfo:
    notFilledUsers = getUnfilledUsers(spending.debtors)
    expressions = list(filter(lambda x: x != '', spending.debtors.values()))
    spendingType, remainingAmount, xValue = calculations.get_spending_meta_info(expressions, spending.costAmount)
    return SpendingMetaInfo(type=spendingType, remainingAmount=remainingAmount, xValue=xValue, notFilledUsers=notFilledUsers)

def getExpressionOfReply(text: str, user: str, spending: Spending) -> str:
    expression = text
    debtor_key = utils.find_username(spending.debtors.keys(), user)
    if len(expression) > 100:
        raise BotException('🤓☝️ Внатуре задрот')
    if expression.startswith('...'):
        if debtor_key == None or len(spending.debtors[debtor_key]) == 0:
            raise BotWrongInputException('Надо указать должников')
        expression = spending.debtors[debtor_key] + expression[3:]
    calculationContext = calculations.ExpressionContext().with_total_sum(spending.costAmount)
    answer = calculations.parse_expression(expression, calculationContext)
    if answer[0] < 0 or answer[0] > spending.costAmount:
        raise BotWrongInputException(f'У должника неверная сумма {answer[0]}')
    return expression

def getUsersFromSpendings(spendings: list[Spending]) -> str:
    users = {}
    for spending in spendings:
        users[utils.normalize_username(spending.telegramFromId)] = spending.telegramFromId
    return "@" + " @".join([users[user] for user in sorted(users.keys())]) if users else ""

def addEvenSpendingForUsers(data: parsers_handler.ParsedQuery, users: list[str]):
    # If no debtors specified, split among all users in the group
    if not data.debtors:
        if not users:
            raise BotWrongInputException('Не указаны должники')
        # Create equal split expressions: s/n for each user
        n = len(users)
        for user in users:
            data.debtors[user] = f's/{n}'
