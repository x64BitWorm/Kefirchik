from queue import PriorityQueue
from datetime import date
import csv
import io
import random
from collections import defaultdict

import utils
from services import calculations
from utils import BotException, normalize_username, timestamp_to_datestr
from services.formatters import formatMoney
from handlers import spendings_handler
from models.dto.report_dto import ReportFileDto, ReportInfoDto, ReportOverviewDto, ReportTransactionDto, MutualBalanceDto
from models.db.spending import Spending

# Возвращает случайную из незавершенных трат
def getUncompletedSpending(spendings: list[Spending]) -> Spending | None:
    uncompletedSpendings = [spending for spending in spendings if not spending.isCompleted]
    return random.choice(uncompletedSpendings) if uncompletedSpendings else None

# Собрать соответствие нормализованных ников исходному регистру
def extractDisplayNames(spendings: list[Spending]) -> dict[str, str]:
    display_names = {}
    usernames_from_messages = set()
    for spending in spendings:
        if not spending.isCompleted:
            continue
        papik = normalize_username(spending.telegramFromId)
        display_names[papik] = spending.telegramFromId
        usernames_from_messages.add(papik)
        for debtor in spending.debtors:
            normalized_debtor = normalize_username(debtor)
            if normalized_debtor not in usernames_from_messages:
                display_names[normalized_debtor] = debtor
    return display_names

# Составить обзор трат: папики, должники, их суммы и балансы
def generateReport(spendings: list[Spending]) -> ReportOverviewDto:
    papiks_totals = defaultdict(int)
    balance_of = defaultdict(int)
    debtors_totals = defaultdict(int)
    display_names = extractDisplayNames(spendings)
    for spending in spendings:
        if not spending.isCompleted:
            continue
        papik = normalize_username(spending.telegramFromId)
        cost = spending.costAmount
        papiks_totals[papik] += cost
        balance_of[papik] += cost
        for debtor, share in spending.debtors.items():
            normalized_debtor = normalize_username(debtor)
            debtors_totals[normalized_debtor] += share
            balance_of[normalized_debtor] -= share
    return ReportOverviewDto(
        papiks=dict(papiks_totals),
        debtors=dict(debtors_totals),
        balances=dict(balance_of),
        display_names=display_names
    )

# Рассчитать взаимные балансы
def calculateMutualBalances(spendings: list[Spending]) -> list[MutualBalanceDto]:
    result = []
    papiks = defaultdict(int)
    for spending in spendings:
        if not spending.isCompleted:
            continue
        papikNick = normalize_username(spending.telegramFromId)
        for debtorNick, share in spending.debtors.items():
            normalizedDebtor = normalize_username(debtorNick)
            if normalizedDebtor == papikNick:
                continue
            key = normalizedDebtor + "\0" + papikNick
            mult = 1
            if normalizedDebtor > papikNick:
                key = papikNick + "\0" + normalizedDebtor
                mult = -1
            papiks[key] += share * mult
    for nicksCombined, share in papiks.items():
        nicks = str(nicksCombined).split("\0")
        if share < 0:
            nicks.reverse()
            share *= -1
        share = round(share, 2)
        if share >= 0.01:
            result.append(MutualBalanceDto(debtor_nick=nicks[0], papik_nick=nicks[1], amount=share))
    return result

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
def generateCsv(spendings: list[Spending]) -> ReportFileDto:
    output = io.StringIO()
    writer = csv.writer(output)

    table1 = generateMainCsv(spendings)
    table2 = generateMutualCsv(spendings)

    for row in utils.align_tables(table1, table2):
        writer.writerow(row)

    csv_content = output.getvalue()
    return ReportFileDto(
        file=b"\xef\xbb\xbf" + csv_content.encode("utf-8"),
        filename=f"Отчёт_{date.today():%Y-%m-%d}.csv"
    )

# Основная таблица с балансами и списком трат
def generateMainCsv(spendings: list[Spending]) -> list[list[str]]:
    overview = generateReport(spendings)
    result = []

    names = list(overview.balances.keys())
    display_names = [overview.displayNames.get(name, name) for name in names]
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
        result.append(row)

    result.append(["Коммент", "Кто", "Сколько"] + display_names + ["Дата"])

    for spending in spendings:
        if not spending.isCompleted:
            continue
        spending_debtors = {
            normalize_username(name): value
            for name, value in spending.debtors.items()
        }
        debt_shares = [
            formatMoney(spending_debtors[name]) if name in spending_debtors else ""
            for name in names
        ]
        result.append([
            spending.desc,
            overview.displayNames.get(normalize_username(spending.telegramFromId), spending.telegramFromId),
            formatMoney(spending.costAmount),
            *debt_shares,
            timestamp_to_datestr(spending.date)
        ])

    return result

# Дополнительная таблица с взаимными балансами (без транзитивности)
def generateMutualCsv(spendings: list[Spending]) -> list[list[str]]:
    mutualBalances = calculateMutualBalances(spendings)
    if not mutualBalances:
        return []
    display_names = extractDisplayNames(spendings)
    debtors = []
    papiks = []
    for mutualBalance in mutualBalances:
        utils.bisect_insert_uniq(debtors, display_names.get(mutualBalance.debtorNick, mutualBalance.debtorNick))
        utils.bisect_insert_uniq(papiks, display_names.get(mutualBalance.papikNick, mutualBalance.papikNick))
    result = [['от\\кому'] + papiks]
    table = [[''] * len(papiks) for _ in range(len(debtors))]
    for mutualBalance in mutualBalances:
        debtorNick = display_names.get(mutualBalance.debtorNick, mutualBalance.debtorNick)
        papikNick = display_names.get(mutualBalance.papikNick, mutualBalance.papikNick)
        debtorIdx = utils.bisect_index_of(debtors, debtorNick)
        papikIdx = utils.bisect_index_of(papiks, papikNick)
        table[debtorIdx][papikIdx] = formatMoney(mutualBalance.amount)
    for i, row in enumerate(table):
        result.append([debtors[i]] + row)
    return result

# Составить вывод о транзакциях
def getReportInfo(spendings: list[Spending]) -> ReportInfoDto:
    report = generateReport(spendings)
    transactions = calculateTransactions(report.balances)
    answer = ''
    if len(transactions) > 0:
        for transaction in transactions:
            if transaction.amount >= 0.01:
                fromNick = report.displayNames.get(transaction.fromNick, transaction.fromNick)
                toNick = report.displayNames.get(transaction.toNick, transaction.toNick)
                answer += f'{fromNick} ➡️ {toNick} {formatMoney(transaction.amount)}🎪\n'
        return ReportInfoDto(transactions_count=len(transactions), text=answer)
    else:
        return ReportInfoDto(transactions_count=0, text='⚠️ Нет записанных трат')

# Составить отчет по трате
def getSpendingReport(spending: Spending) -> str:
    result = f'Сумма: {formatMoney(spending.costAmount)}\n'
    x_value: float | None = None
    if spending.isCompleted:
        metaInfo = spendings_handler.getSpendingMetaInfo(spending)
        x_value = metaInfo.xValue
        if x_value == 0.0 or x_value == None:
            result += 'Трата завершена\n'
        else:
            result += f'x = {x_value}\n'
    debtors = spending.debtors
    for debtor, value in debtors.items():
        if value == '':
            result += f'\n@{debtor} не заполнил'
            continue
        context = calculations.ExpressionContext().with_total_sum(spending.costAmount)
        b_value, a_value = calculations.parse_expression(value, context)
        valueStr = value
        explainStr = f'{formatMoney(b_value)}'
        if a_value != 0.0:
            explainStr += f' + {formatMoney(float(a_value))}x'
        if a_value == 0.0:
            valueStr = formatMoney(b_value)
        elif x_value != None:
            valueStr = formatMoney(b_value + a_value * x_value)
        result += f'\n@{debtor}'
        if len(valueStr):
            result += f' {valueStr}'
        if valueStr != explainStr and len(explainStr):
            result += f' ({explainStr})'
    return result

# Составить текст о незавершённой трате
def getUncompletedWarningText(uncompletedSpending: Spending) -> str:
    unfilledUsers = spendings_handler.getUnfilledUsers(uncompletedSpending.debtors)
    if unfilledUsers:
        return '❗️ Есть незакрытая трата у' + ' @'.join(['']+unfilledUsers) + '\n\n'
    # Все доли заполнены, поэтому предупреждаем всех участников о расхождении
    try:
        calculations.calculate_spendings(uncompletedSpending.debtors.values(), uncompletedSpending.costAmount)
    except BotException as error:
        users = list(uncompletedSpending.debtors)
        if normalize_username(uncompletedSpending.telegramFromId) not in map(normalize_username, users):
            users.append(uncompletedSpending.telegramFromId)
        return '@' + ' @'.join(users) + f', в вашей трате {str(error).lower()}\n\n'
