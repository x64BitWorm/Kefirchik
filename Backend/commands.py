from telegram import ForceReply, Update, constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext
import database
import json
import parsers
import utils
import reports
import io
from datetime import date

addMessage = None
respMessage = None

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Добавление новой траты"""
    try:
        global addMessage
        addMessage = update.message
        message = 'Запомнил🍶' + ' ждем' + ' @Random_Name0, @John_Doe'
        await update.message.reply_text(message, reply_markup=getCancelMarkup())
    except Exception as e:
        print("Error: ", e)
        await update.message.set_reaction(constants.ReactionEmoji.CRYING_FACE)

exprs = ["1000", "(1000) + (2/3*450)", "(1000) + (2/3*450) + (x)","(1000) + (2/3*450) + (x)", "100+900+1/3*2*450+400", "42"]
cnt = 0
must_delete = None
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Добавление незаполненного должника"""
    global cnt
    global exprs
    global respMessage
    global must_delete
    respMessage = update.message
    print(cnt)
    if update.message.text[0] == '4':
        message = """Трата обновлена. Ваша трата: 42""" 
        await update.message.reply_text(message, reply_markup=getSuccessMarkup(True))
    elif cnt == 0 :
        message = """Трата обновлена. Ваша трата: """ + exprs[cnt]
        await update.message.reply_text(message, reply_markup=getSuccessMarkup(True))
    elif update.message.text[0] == '+':
        message = """Трата обновлена. Ваша трата:""" + exprs[cnt]
        await update.message.reply_text(message, reply_markup=getSuccessMarkup(True))
    else:
        message = """Вы действительно хотите перезаписать трату новой записью?
⚠️ При перезаписи все предыдущие ваши записи по данной трате будут удалены ⚠️"""
        must_delete = await update.message.reply_text(message, reply_markup=getTryRewriteMarkup())
    cnt += 1
    return
    group = database.getGroup(update.message.chat_id)
    cost = database.getCost(group['id'], update.message.reply_to_message.id)
    username = update.message.from_user.username
    debs = json.loads(cost['debtors'])
    try:
        answer = utils.calculations.parse_expression(update.message.text)
        if answer[0] < 0 or answer[0] > cost['costAmount']:
            raise
    except:
        await update.message.set_reaction(constants.ReactionEmoji.CLOWN_FACE)
        return
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


async def reset_cur_callback(update: Update, ctx: CallbackContext) -> None:
    global respMessage
    query = update.callback_query
    message = 'Снова ждем @Random_Name_0'
    await ctx.bot.deleteMessage (message_id = must_delete.message_id,chat_id = respMessage.chat_id)
    await respMessage.reply_text('Трата успешно сброшена', reply_markup=getSuccessMarkup(False))
    await addMessage.reply_text(message)
    await query.answer()

async def rewrite_cur_callback(update: Update, ctx: CallbackContext) -> None:
    global cnt
    global exprs
    global must_delete
    query = update.callback_query
    message = """Трата обновлена. Ваша трата: """ + exprs[cnt]
    await ctx.bot.deleteMessage (message_id = must_delete.message_id,chat_id = respMessage.chat_id)
    must_delete = await respMessage.reply_text(message, reply_markup=getSuccessMarkup(True))
    await query.answer()

async def add_cur_callback(update: Update, ctx: CallbackContext) -> None:
    global cnt
    global exprs
    query = update.callback_query
    message = """Трата обновлена. Ваша трата: """ + exprs[cnt]
    await ctx.bot.deleteMessage (message_id = must_delete.message_id,chat_id = respMessage.chat_id)
    await respMessage.reply_text(message, reply_markup=getSuccessMarkup(True))
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

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = """
Привет! Это бот для расчета совместных трат

* тот кто платил вызывает команду add (удерживает ее в тг пальцем) и пишет сумму которую потратил через пробел.
потом тэгает на каждой новой строчке чела и через пробел пишет сколько он потратил.
* а еще мы добавили немного задротства, поэтому в выражении кто скока потратил можно писать не просто число, а целое выражение (например 100+50/2), и даже переменную x,
для добавления общей траты (например если пили общий чай, то можно написать что типа Артем потратил 300+x, где 300 его личные траты, а x это чтото общее).
все строчки в add которые не начинаются с тэга это комменты (например "за пончики").
* ну и после того как добавили все траты можно дернуть команду report и она выплюнет кто скока кому переводит бабок.
* а команда reset (ну очень опасная) удаляет все траты и их придеца заполнять заново

пример:
/add@kefirchik42_bot 1500
@x64BitWorm 500+x
@Artem_Barsov 300+x
@Grisha_Barsov 100
@Random_Name_0 100
"""
    await update.message.reply_text(message)

def getCsvReportMarkup():
    return InlineKeyboardMarkup([[InlineKeyboardButton('Отчет.csv', callback_data="report-csv")]])

def getTryRewriteMarkup():
    return InlineKeyboardMarkup([[InlineKeyboardButton('Перезаписать трату', callback_data='rewrite-cur')], [InlineKeyboardButton('Дополнить трату записью', callback_data='add-cur')], [InlineKeyboardButton('Отмена', callback_data='cancel-send')]])

def getCancelMarkup():
    return InlineKeyboardMarkup([[InlineKeyboardButton('Отмена', callback_data='cancel-send')]])

def getSuccessMarkup(withCancel: bool):
    if withCancel:
        return InlineKeyboardMarkup([[InlineKeyboardButton('Сбросить всю трату', callback_data='reset-cur')], [InlineKeyboardButton('Отмена', callback_data='cancel-send')]])
    else:
        return InlineKeyboardMarkup([[InlineKeyboardButton('Отмена', callback_data='cancel-send')]])

def getResetMarkup():
    return InlineKeyboardMarkup([[InlineKeyboardButton('Подтверждаю сброс', callback_data='reset-costs')]])
