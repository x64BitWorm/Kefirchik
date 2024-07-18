from queue import PriorityQueue

# trati - [{'amount', 'papik', 'debtors': {name: amount}}]
# returns - dict<name>{amount}, {papiks, debtors, balance}
def generateReport(trati):
    data = {'papiks':{}, 'debtors':{}, 'balances':{}}
    for trata in trati:
        amount = trata['amount']
        if trata['creditor'] not in data['papiks']:
            data['papiks'][trata['creditor']] = 0
        data['papiks'][trata['creditor']] += trata['amount']
        if trata['creditor'] not in data['balances']:
            data['balances'][trata['creditor']] = 0
        data['balances'][trata['creditor']] += trata['amount']
        for debtor, debt in trata['debtors'].items():
            if debtor not in data['debtors']:
                data['debtors'][debtor] = 0
            data['debtors'][debtor] += debt
            if debtor not in data['balances']:
                data['balances'][debtor] = 0
            data['balances'][debtor] -= debt
            amount -= debt
        if abs(amount) >= 0.01:
            raise ValueError('Штаны не сошлись! сумма долгов в трате не равна деньгам папика')
    return data

# balances - {name: amount}
# returns - {from, to, amount}[]
def calculateTransactions(balances):
    balanceCheck = sum(balances.values())
    if abs(balanceCheck) >= 0.01:
        raise ValueError('Штаны чашек не сходятся! (сумма должна быть 0), а щас: ' + str(balanceCheck))
    papiks = PriorityQueue()
    for k, v in dict(filter(lambda x:x[1]>0, balances.items())).items():
        papiks.put((-v, k))
    doljniks = PriorityQueue()
    for k, v in dict(filter(lambda x:x[1]<0, balances.items())).items():
        doljniks.put((v, k))
    transactions = []
    while not papiks.empty() or not doljniks.empty():
        doljnik = {}
        doljnik['amount'], doljnik['name'] = doljniks.get()
        papik = {}
        papik['amount'], papik['name'] = papiks.get()
        amount = min(-papik['amount'], -doljnik['amount'])
        transactions.append({'from': doljnik['name'],
                             'to': papik['name'],
                             'amount': amount
                            })
        if -papik['amount'] < -doljnik['amount']:
            doljniks.put((doljnik['amount']+amount, doljnik['name']))
        elif -papik['amount'] > -doljnik['amount']:
            papiks.put((papik['amount'] + amount, papik['name']))
    return transactions

# spendings, report, transactions
# returns stringIO document
def generateCsv(spendings, report, transactions):
    # TODO
    pass
