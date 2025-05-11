from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def getCsvReportMarkup():
    return InlineKeyboardMarkup([[InlineKeyboardButton('Отчет.csv', callback_data="report-csv")]])

def getResetMarkup():
    return InlineKeyboardMarkup([[InlineKeyboardButton('Подтверждаю сброс', callback_data='reset-costs')]])
