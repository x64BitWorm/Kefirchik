import json
import calculations
import random

def checkCostState(debtors):
    debtors = json.loads(debtors)
    names = []
    for k, v in debtors.items():
        if not v:
            names.append(k)
    return names

def setDebtersFinalValues(debters, amount):
    ans = calculations.calculate_spendings(debters.values(), amount)
    for i, (k, v) in enumerate(debters.items()):
        debters[k] = ans[i]
    return json.dumps(debters)

def getUncompletedSpending(spendings):
    unCompleted = []
    for item in spendings:
        if item['isCompleted'] == 0:
            unCompleted.append(item)
    if len(unCompleted) == 0:
        return None
    return random.choice(unCompleted)

def convertSpendingsToReportDto(spendings):
    return list(map(lambda record: {
        'amount': record['costAmount'],
        'creditor': record['telegramFromId'],
        'debtors': json.loads(record['debtors']),
        'comment': record['desc'],
    }, spendings))