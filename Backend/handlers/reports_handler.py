from queue import PriorityQueue
from datetime import date
import csv
import io
import random

from models.dto.report_dto import ReportInfoDto, ReportOverviewDto, ReportTransactionDto
from models.db.spending import Spending

# Возвращает случайную из незавершенных трат
def getUncompletedSpending(spendings: list[Spending]) -> Spending | None:
    unCompleted = []
    for item in spendings:
        if item.isCompleted == 0:
            unCompleted.append(item)
    if len(unCompleted) == 0:
        return None
    return random.choice(unCompleted)

# trati - [{'amount', 'papik', 'debtors': {name: amount}}]
# returns - {'papiks': {name: amount}, 'debtors': {name: amount}, 'balances': {name: amount}}
def generateReport(trati: list[Spending]) -> ReportOverviewDto:
    data = ReportOverviewDto()
    for trata in trati:
        amount = trata.costAmount
        if trata.telegramFromId not in data.papiks:
            data.papiks[trata.telegramFromId] = 0
        data.papiks[trata.telegramFromId] += trata.costAmount
        if trata.telegramFromId not in data.balances:
            data.balances[trata.telegramFromId] = 0
        data.balances[trata.telegramFromId] += trata.costAmount
        for debtor, debt in trata.debtors.items():
            if debtor not in data.debtors:
                data.debtors[debtor] = 0
            data.debtors[debtor] += debt
            if debtor not in data.balances:
                data.balances[debtor] = 0
            data.balances[debtor] -= debt
            amount -= debt
        if not trata.isCompleted:
            raise ValueError('Трата не завершена')
    return data

# balances - {name: amount}
# returns - [{'from', 'to', 'amount'}]
def calculateTransactions(balances: dict[str, float]) -> list[ReportTransactionDto]:
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
        transactions.append(ReportTransactionDto(from_nick=doljnik['name'], to_nick=papik['name'], amount=amount))
        if -papik['amount'] < -doljnik['amount']:
            doljniks.put((doljnik['amount']+amount, doljnik['name']))
        elif -papik['amount'] > -doljnik['amount']:
            papiks.put((papik['amount'] + amount, papik['name']))
    return transactions

# spendings, report, transactions
# returns stringIO document
def generateCsv(spendings: list[Spending]) -> io.StringIO:
    report = generateReport(spendings)
    doc = io.StringIO()
    writer = csv.writer(doc)
    names = list(report.balances.keys())
    nameId = {name: id for id, name in enumerate(names)}
    
    l = [''] * len(names)
    for papik, amount in report.papiks.items():
        l[nameId[papik]] = round(amount, 2)
    writer.writerow(['', 'Всего', 'заплатил'] + l)

    l = [''] * len(names)
    for debtor, amount in report.debtors.items():
        l[nameId[debtor]] = round(amount, 2)
    writer.writerow(['', '', 'должен заплатить'] + l)
    
    l = [''] * len(names)
    for balance, amount in report.balances.items():
        l[nameId[balance]] = round(amount, 2)
    writer.writerow(['', '', 'баланс'] + l)

    writer.writerow(['Наименование', 'Кто', 'Сколько'] + list(report.balances.keys()) + ['Дата'])
    for trata in spendings:
        debts = [''] * len(names)
        for debtor, amount in trata.debtors.items():
            debts[nameId[debtor]] = round(amount, 2)
        writer.writerow([trata.desc, trata.telegramFromId, round(trata.costAmount, 2)] + debts + [trata.date])
    doc = io.StringIO('\ufeff' + doc.getvalue()) # UTF-8 BOM
    doc.name = f'Отчет_{date.today()}.csv'
    doc.seek(0)
    return doc

def getReportInfo(spendings: list[Spending]) -> ReportInfoDto:
    report = generateReport(spendings)
    transactions = calculateTransactions(report.balances)
    answer = ''
    if len(transactions) > 0:
        for transaction in transactions:
            if transaction.amount >= 0.01:
                answer += f'{transaction.fromNick} ➡️ {transaction.toNick} {round(transaction.amount, 2)}🎪\n'
        return ReportInfoDto(len(transactions), answer)
    else:
        return ReportInfoDto(0, '⚠️ Нет записанных трат')
