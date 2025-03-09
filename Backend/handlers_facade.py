import parsers
from handlers.help_handler import *
import handlers.spendings_handler as spendings_handler
import handlers.help_handler as help_handler
from message import IMessage
from telegram import ForceReply, Update, constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext
from database import IDatabase
from message import TgMessage

class HandlersFacade:
    def __init__(self, db: IDatabase):
        self.db = db

    async def start_command(self, message: IMessage) -> None:
        await message.reply_text(help_handler.getHelpText())

    async def add_command(self, message: IMessage) -> None:
        data = parsers.ParsedQuery(message)
        reply_text = spendings_handler.getReplyText(data)
        spendingCompleted = spendings_handler.isSpendingCompleted(data)
        debtors = spendings_handler.getDebtorsWithAmounts(data.debtors, data.amount) if spendingCompleted else data.debtors
        reply_message_id = await message.reply_text(reply_text, InlineKeyboardMarkup([[InlineKeyboardButton('Отмена', callback_data='cancel-send')]]))
        self.db.insertCost(reply_message_id, message.getChatId(), spendingCompleted, message.getUsername(), data.amount, debtors, data.desc)

    async def reply_command(self, message: IMessage) -> None:
        pass
