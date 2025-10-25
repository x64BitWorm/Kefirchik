from queue import PriorityQueue
from datetime import date
import csv
import io
import random
from collections import defaultdict

from utils import timestamp_to_datestr
from services.formatters import formatMoney
from handlers import spendings_handler
from models.dto.report_dto import ReportInfoDto, ReportOverviewDto, ReportTransactionDto
from models.db.spending import Spending

# Возвращает случайную из незавершенных трат
def getUncompletedSpending(spendings: list[Spending]) -> Spending | None:
    uncompletedSpendings = [spending for spending in spendings if not spending.isCompleted]
    return random.choice(uncompletedSpendings) if uncompletedSpendings else None

# Составить обзор трат: папики, должники, их суммы и балансы
def generateReport(spendings: list[Spending]) -> ReportOverviewDto:
    papiks_totals = defaultdict(int)
    balance_of = defaultdict(int)
    debtors_totals = defaultdict(int)
    for spending in spendings:
        if not spending.isCompleted:
            continue
        papik = spending.telegramFromId
        cost = spending.costAmount
        papiks_totals[papik] += cost
        balance_of[papik] += cost
        for debtor, share in spending.debtors.items():
            debtors_totals[debtor] += share
            balance_of[debtor] -= share
    return ReportOverviewDto(
        papiks=dict(papiks_totals),
        debtors=dict(debtors_totals),
        balances=dict(balance_of)
    )

# Составить список транзакций
def calculateTransactions(balances: dict[str, float]) -> list[ReportTransactionDto]:
    papiks = PriorityQueue()
    debtors = PriorityQueue()
    # the values negated for correct ordering
    for user, amount in balances.items():
        if amount > 0:
            papiks.put((-amount, user))
        elif amount < 0:
            debtors.put((amount, user))
    transactions: list[ReportTransactionDto] = []
    while not papiks.empty() and not debtors.empty():
        debt_amount, debtor = debtors.get()
        papik_amount, papik = papiks.get()
        debt_amount = -debt_amount
        papik_amount = -papik_amount
        amount = min(papik_amount, debt_amount)
        transactions.append(ReportTransactionDto(
            from_nick=debtor,
            to_nick=papik,
            amount=amount
        ))
        if papik_amount > amount:
            papiks.put((-(papik_amount - amount), papik))
        elif debt_amount > amount:
            debtors.put((-(debt_amount - amount), debtor))
    return transactions

# Сгенерить csv по всем завершённым тратам
def generateCsv(spendings: list[Spending]) -> io.StringIO:
    overview = generateReport(spendings)
    output = io.StringIO()
    writer = csv.writer(output)

    names = list(overview.balances.keys())
    summary_rows = [
        ("", "Всего",         "заплатил", overview.papiks),
        ("",      "", "должен заплатить", overview.debtors),
        ("",      "",           "баланс", overview.balances),
    ]
    for _, col2, col3, data in summary_rows:
        row = ["", col2, col3] + [
            formatMoney(data[name]) if name in data else "" 
            for name in names
        ]
        writer.writerow(row)

    writer.writerow(["Коммент", "Кто", "Сколько"] + names + ["Дата"])

    for spending in spendings:
        if not spending.isCompleted:
            continue
        debt_shares = [
            formatMoney(spending.debtors[name]) if name in spending.debtors else ""
            for name in names
        ]
        writer.writerow([
            spending.desc,
            spending.telegramFromId,
            formatMoney(spending.costAmount),
            *debt_shares,
            timestamp_to_datestr(spending.date)
        ])

    csv_content = output.getvalue()
    final_io = io.StringIO("\ufeff" + csv_content)
    final_io.name = f"Отчёт_{date.today():%Y-%m-%d}.csv"
    final_io.seek(0)
    return final_io

# Составить вывод о транзакциях
def getReportInfo(spendings: list[Spending]) -> ReportInfoDto:
    report = generateReport(spendings)
    transactions = calculateTransactions(report.balances)
    answer = ''
    if len(transactions) > 0:
        for transaction in transactions:
            if transaction.amount >= 0.01:
                answer += f'{transaction.fromNick} ➡️ {transaction.toNick} {formatMoney(transaction.amount)}🎪\n'
        return ReportInfoDto(transactions_count=len(transactions), text=answer)
    else:
        return ReportInfoDto(transactions_count=0, text='⚠️ Нет записанных трат')

# Составить текст о незавершённой трате
def getUncompletedWarningText(uncompletedSpending: Spending) -> str:
    unfilledUsers = spendings_handler.getUnfilledUsers(uncompletedSpending.debtors)
    return '❗️ Есть незакрытая трата у' + ' @'.join(['']+unfilledUsers) + '\n\n'
