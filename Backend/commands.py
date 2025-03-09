from telegram import ForceReply, Update, constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext
import database
import json
import parsers
import utils
import reports
import io
from datetime import date

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Добавление незаполненного должника"""
    group = database.getGroup(update.message.chat_id)
    cost = database.getCost(group['id'], update.message.reply_to_message.id)
    username = update.message.from_user.username
    debs = json.loads(cost['debtors'])
    expression = str(update.message.text)
    try:
        if len(expression) > 100:
            await update.message.reply_text('🤓☝️ Внатуре задрот')
            raise
        if expression.startswith('...'):
            if len(debs[username]) == 0:
                raise
            expression = debs[username] + expression[3:]
        answer = utils.calculations.parse_expression(expression)
        if answer[0] < 0 or answer[0] > cost['costAmount']:
            raise
    except:
        await update.message.set_reaction(constants.ReactionEmoji.CLOWN_FACE)
        return
    debs[username] = expression
    debs = json.dumps(debs)
    notFilled = utils.checkCostState(debs)
    completed = len(notFilled) == 0
    if completed:
        try:
            debs = utils.setDebtersFinalValues(json.loads(debs), cost['costAmount'])
        except:
            await update.message.set_reaction(constants.ReactionEmoji.CRYING_FACE)
            return
    database.updateCost(group['id'], update.message.reply_to_message.id, completed, debs)
    await update.message.set_reaction(constants.ReactionEmoji.FIRE if completed else constants.ReactionEmoji.THUMBS_UP)
    if completed:
        await post_cost_completed(update.message.reply_to_message.id, update)

async def post_cost_completed(messageId, update: Update):
    pass

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создания отчетов трат"""
    group = database.getGroup(update.message.chat_id)
    spendings = database.getSpendings(group['id'])
    uncompletedSpending = utils.getUncompletedSpending(spendings)
    if uncompletedSpending != None:
        notFilled = utils.checkCostState(uncompletedSpending['debtors'])
        await update.message.reply_text('Сначала завершите трату'+' @'.join(['']+notFilled), reply_to_message_id=uncompletedSpending['messageId'])
        return
    try:
        spendings = utils.convertSpendingsToReportDto(spendings)
        report = reports.generateReport(spendings)
        transactions = reports.calculateTransactions(report['balances'])
        answer = ''
        if len(transactions) > 0:
            for transaction in transactions:
                if transaction["amount"] >= 0.01:
                    answer += f'{transaction["from"]} ➡️ {transaction["to"]} {round(transaction["amount"], 2)}🎪\n'
            await update.message.reply_text(answer, reply_markup=getCsvReportMarkup())
        else:
            await update.message.reply_text('⚠️ Нет записанных трат')
    except Exception as e:
        await update.message.reply_text('⚠️ ' + str(e))
        raise e
    
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Сброс истории трат"""
    group = database.getGroup(update.message.chat_id)
    costs = database.getSpendings(group['id'])
    users = ",".join(set(map(lambda x: x['telegramFromId'], costs)))
    if not users:
        database.removeCosts(update.message.chat_id)
    else:
        await update.message.reply_text(users, reply_markup=getResetMarkup())

async def report_csv_callback(update: Update, ctx: CallbackContext) -> None:
    query = update.callback_query
    group = database.getGroup(query.message.chat_id)
    spendings = database.getSpendings(group['id'])
    spendings = utils.convertSpendingsToReportDto(spendings)
    doc = reports.generateCsv(spendings)
    await query.message.reply_document(document=doc, caption='Ваш отчет готов 📈 @' + query.from_user.username)
    await query.answer()

async def cancel_callback(update: Update, ctx: CallbackContext) -> None:
    query = update.callback_query
    chat = query.message.chat.id
    message = query.message.message_id
    cost = database.getCost(chat, message)
    if query.from_user.username == cost['telegramFromId']:
        database.removeCost(chat, message)
        await query.message.delete()
    await query.answer()

async def reset_callback(update: Update, ctx: CallbackContext) -> None:
    query = update.callback_query
    fromUser = query.from_user.username
    chat = query.message.chat.id
    message = query.message.text
    users = message.split(",")
    await query.answer()
    users.remove(fromUser)
    if not users:
        database.removeCosts(chat)
        await query.message.edit_text("Траты сброшены💨")
        return
    users = ",".join(users)
    await query.message.edit_text(users, reply_markup=getResetMarkup())


def getCsvReportMarkup():
    return InlineKeyboardMarkup([[InlineKeyboardButton('Отчет.csv', callback_data="report-csv")]])

def getResetMarkup():
    return InlineKeyboardMarkup([[InlineKeyboardButton('Подтверждаю сброс', callback_data='reset-costs')]])
