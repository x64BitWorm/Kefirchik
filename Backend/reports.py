from queue import PriorityQueue
from datetime import date
import csv
import io

# trati - [{'amount', 'papik', 'debtors': {name: amount}}]
# returns - {'papiks': {name: amount}, 'debtors': {name: amount}, 'balances': {name: amount}}
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
        if not trata['isCompleted']:
            raise ValueError('Трата не завершена')
    return data

# balances - {name: amount}
# returns - [{'from', 'to', 'amount'}]
def calculateTransactions(balances):
    papiks = PriorityQueue()
    for k, v in dict(filter(lambda x:x[1]>0, balances.items())).items():
        papiks.put((-v, k))
    doljniks = PriorityQueue()
    for k, v in dict(filter(lambda x:x[1]<0, balances.items())).items():
        doljniks.put((v, k))
    transactions = []
    while not papiks.empty() and not doljniks.empty():
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
def generateCsv(spendings):
    report = generateReport(spendings)
    doc = io.StringIO()
    writer = csv.writer(doc)
    names = list(report['balances'].keys())
    nameId = {name: id for id, name in enumerate(names)}
    
    l = [''] * len(names)
    for papik, amount in report['papiks'].items():
        l[nameId[papik]] = amount
    writer.writerow(['', 'Всего', 'заплатил'] + l)

    l = [''] * len(names)
    for debtor, amount in report['debtors'].items():
        l[nameId[debtor]] = amount
    writer.writerow(['', '', 'должен заплатить'] + l)
    
    l = [''] * len(names)
    for balance, amount in report['balances'].items():
        l[nameId[balance]] = amount
    writer.writerow(['', '', 'баланс'] + l)

    writer.writerow(['Наименование', 'Кто', 'Сколько'] + list(report['balances'].keys()) + ['Дата'])
    for trata in spendings:
        debts = [''] * len(names)
        for debtor, amount in trata['debtors'].items():
            debts[nameId[debtor]] = amount
        writer.writerow([trata['comment'], trata['creditor'], trata['amount']] + debts + [trata['date']])
    doc = io.StringIO('\ufeff' + doc.getvalue()) # UTF-8 BOM
    doc.name = f'Отчет_{date.today()}.csv'
    doc.seek(0)
    return doc