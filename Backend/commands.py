from telegram import ForceReply, Update, constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext
import database
import json
import parsers
import calculations
import utils
import reports
import io
from datetime import date

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Добавление новой траты"""
    group = database.getGroup(update.message.chat_id)
    data = parsers.ParsedQuery(update.message.text)
    debs = json.dumps(data.debters)
    notFilled = utils.checkCostState(debs)
    completed = len(notFilled) == 0
    message = 'Запомнил🍶'
    if not completed:
        message += ' ждем' + ' @'.join([''] + notFilled)
    else:
        debs = utils.setDebtersFinalValues(data.debters, data.amount)
    rep = await update.message.reply_text(message)
    database.insertCost(rep.id, update.message.chat_id, completed, update.message.from_user.username, data.amount, debs, data.desc)
    if completed:
        await post_cost_completed(rep.id, update)

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Добавление незаполненного должника"""
    group = database.getGroup(update.message.chat_id)
    cost = database.getCost(group['id'], update.message.reply_to_message.id)
    username = update.message.from_user.username
    debs = json.loads(cost['debtors'])
    debs[username] = update.message.text
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
    #cost = database.getCost(messageId)
    #text = f'По итогу {cost["costAmount"]}\n'
    #for k, v in json.loads(cost["debtors"]).items():
    #    text += f'{k}: {v}'
    #await update.message.reply_text(text)

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создания отчетов трат"""
    group = database.getGroup(update.message.chat_id)
    spendings = database.getSpendings(group['id'])
    uncompletedSpending = utils.getUncompletedSpending(spendings)
    if uncompletedSpending != None:
        await update.message.reply_text('Сначала завершите трату', reply_to_message_id=uncompletedSpending['messageId'])
        return
    try:
        spendings = utils.convertSpendingsToReportDto(spendings)
        report = reports.generateReport(spendings)
        transactions = reports.calculateTransactions(report['balances'])
        answer = ''
        for transaction in transactions:
            answer += f'{transaction["from"]} ➡️ {transaction["to"]} {transaction["amount"]}🎪\n'
        await update.message.reply_text(answer, reply_markup=getCsvReportMarkup())
    except Exception as e:
        await update.message.reply_text('⚠️ ' + str(e))
        raise e
    
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Сброс истории трат"""
    group = database.getGroup(update.message.chat_id)
    database.removeCosts(group['id'])
    await update.message.reply_text("Все траты очищены!")

async def report_csv_callback(update: Update, ctx: CallbackContext) -> None:
    query = update.callback_query
    doc = io.StringIO('coming soon!')
    doc.name = f'Отчет_{date.today()}.csv'
    await query.message.reply_document(document=doc,caption='Ваш отчет готов 📈')
    query.answer()

def getCsvReportMarkup():
    return InlineKeyboardMarkup([[InlineKeyboardButton('Отчет.csv', callback_data="report-csv")]])
