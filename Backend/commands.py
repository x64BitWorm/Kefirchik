from telegram import ForceReply, Update, constants
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import database
import json
import parsers
import calculations
import utils

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
    cost = database.getCost(update.message.reply_to_message.id)
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
    database.updateCost(update.message.reply_to_message.id, completed, debs)
    await update.message.set_reaction(constants.ReactionEmoji.FIRE if completed else constants.ReactionEmoji.THUMBS_UP)
    if completed:
        await post_cost_completed(update.message.reply_to_message.id, update)

async def post_cost_completed(messageId, update: Update):
    cost = database.getCost(messageId)
    text = f'По итогу {cost["costAmount"]}\n'
    for k, v in json.loads(cost["debtors"]).items():
        text += f'{k}: {v}'
    await update.message.reply_text(text)

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создания отчетов трат"""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Сброс истории трат"""
    await update.message.reply_text("Help!")

