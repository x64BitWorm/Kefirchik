import json
from handlers import reports_handler
from services.telegram_markups import getCsvReportMarkup, getResetMarkup
from utils import BotException
import services.parsers as parsers
from handlers.help_handler import *
import handlers.spendings_handler as spendings_handler
import handlers.help_handler as help_handler
from models.bot_api.bot_api_interfaces import IMessage
from telegram import constants, InlineKeyboardButton, InlineKeyboardMarkup
from database import IDatabase

class HandlersFacade:
    def __init__(self, db: IDatabase):
        self.db = db

    async def start_command(self, message: IMessage) -> None:
        await message.reply_text(help_handler.getHelpText())

    async def add_command(self, message: IMessage) -> None:
        data = parsers.ParsedQuery(message.getText(), message.getUsername())
        reply_text = spendings_handler.getReplyText(data)
        spendingCompleted = spendings_handler.isSpendingCompleted(data.debtors)
        debtors = spendings_handler.getDebtorsWithAmounts(data.debtors, data.amount) if spendingCompleted else data.debtors
        reply_message_id = await message.reply_text(reply_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Отмена', callback_data='cancel-send')]]))
        self.db.insertCost(reply_message_id, message.getChatId(), spendingCompleted, message.getUsername(), data.amount, debtors, data.comment)

    async def reply_command(self, message: IMessage) -> None:
        group_id = self.db.getGroup(message.getChatId()).id
        spending = self.db.getCost(group_id, message.getReplyMessageId())
        if spending is None:
            return
        expression = spendings_handler.getExpressionOfReply(message.getText(), message.getUsername(), spending)
        spending.debtors[message.getUsername()] = expression
        completed = spendings_handler.isSpendingCompleted(spending.debtors)
        if completed:
            spending.debtors = spendings_handler.getDebtorsWithAmounts(spending.debtors, spending.costAmount) # resolve x's
        self.db.updateCost(group_id, message.getReplyMessageId(), completed, json.dumps(spending.debtors))
        await message.set_reaction(constants.ReactionEmoji.FIRE if completed else constants.ReactionEmoji.THUMBS_UP)
    
    async def report_command(self, message: IMessage) -> None:
        group = self.db.getGroup(message.getChatId())
        spendings = self.db.getSpendings(group.id)

        report = reports_handler.getReportInfo(spendings)
        if report.transactions_count > 0:
            uncompletedSpending = reports_handler.getUncompletedSpending(spendings)
            warningUncompleted = ''
            reply_to_message_id = None
            if uncompletedSpending != None:
                warningUncompleted = reports_handler.getUncompletedWarningText(uncompletedSpending)
                reply_to_message_id = uncompletedSpending.messageId
            await message.reply_text(warningUncompleted + report.text, reply_markup=getCsvReportMarkup(), reply_to_message_id=reply_to_message_id)
        else:
            await message.reply_text(report.text)

    async def reset_command(self, message: IMessage) -> None:
        group_id = self.db.getGroup(message.getChatId()).id
        spendings = self.db.getSpendings(group_id)
        users = spendings_handler.getUsersFromSpendings(spendings) # [Think] get Users From current session, not a list of spendings
        if not users:
            self.db.removeCosts(message.getChatId())
        else:
            await message.reply_text(users, reply_markup=getResetMarkup())
