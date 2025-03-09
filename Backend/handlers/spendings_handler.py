import calculations
import json
from database import IDatabase
from parsers import ParsedQuery

def isSpendingCompleted(data: ParsedQuery):
    notFilledUsers = getUnfilledUsers(data.debtors)
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
