from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def getCsvReportMarkup():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Отчет.csv', callback_data="report-csv")]])

def getResetMarkup():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Подтверждаю сброс', callback_data='reset-costs')]])

def getCancelMarkup():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Отмена', callback_data='cancel-send')]])

def getLastDebtorApproveMarkup():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Да', callback_data="last-debtor-approve/yes"),
                                  InlineKeyboardButton(text='Нет', callback_data="last-debtor-approve/no")]])
