from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def getCsvReportMarkup():
    return InlineKeyboardMarkup([[InlineKeyboardButton('Отчет.csv', callback_data="report-csv")]])

def getResetMarkup():
    return InlineKeyboardMarkup([[InlineKeyboardButton('Подтверждаю сброс', callback_data='reset-costs')]])

def getLastDebtorApproveMarkup():
    return InlineKeyboardMarkup([[InlineKeyboardButton('Да', callback_data="last-debtor-approve/yes"),
                                  InlineKeyboardButton('Нет', callback_data="last-debtor-approve/no")]])
