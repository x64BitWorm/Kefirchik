import json
import calculations

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
