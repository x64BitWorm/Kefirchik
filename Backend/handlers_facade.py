import json
import utils
import reports
from services.telegram_markups import getCsvReportMarkup, getResetMarkup
from utils import BotException
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
        data = parsers.ParsedQuery(message.getText(), message.getUsername())
        reply_text = spendings_handler.getReplyText(data)
        spendingCompleted = spendings_handler.isSpendingCompleted(data.debtors)
        debtors = spendings_handler.getDebtorsWithAmounts(data.debtors, data.amount) if spendingCompleted else data.debtors
        reply_message_id = await message.reply_text(reply_text, InlineKeyboardMarkup([[InlineKeyboardButton('Отмена', callback_data='cancel-send')]]))
        self.db.insertCost(reply_message_id, message.getChatId(), spendingCompleted, message.getUsername(), data.amount, debtors, data.comment)

    async def reply_command(self, message: IMessage) -> None:
        group_id = self.db.getGroup(message.getChatId()).id
        spending = self.db.getCost(group_id,  message.getReplyMessageId())    
        expression = spendings_handler.getExpressionOfReply(message.getText(), message.getUsername(), spending)
        spending.debtors[message.getUsername()] = expression
        completed = spendings_handler.isSpendingCompleted(spending.debtors)
        if completed:
            spending.debtors = spendings_handler.getDebtorsWithAmounts(spending.debtors, spending.costAmount) # resolve x's
        self.db.updateCost(group_id, message.getReplyMessageId(), completed, json.dumps(spending.debtors))
        await message.set_reaction(constants.ReactionEmoji.FIRE if completed else constants.ReactionEmoji.THUMBS_UP)
    
    async def report_command(self, message: IMessage) -> None:
        # rewrite
        group = self.db.getGroup(message.getChatId())
        spendings = self.db.getSpendings(group.id)
        uncompletedSpending = utils.getUncompletedSpending(spendings)
        if uncompletedSpending != None:
            notFilled = utils.checkCostState(uncompletedSpending['debtors'])
            await message.reply_text('Сначала завершите трату'+' @'.join(['']+notFilled), reply_to_message_id=uncompletedSpending['messageId'])
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
                await message.reply_text(answer, reply_markup=getCsvReportMarkup())
            else:
                await message.reply_text('⚠️ Нет записанных трат')
        except Exception as e:
            raise BotException('⚠️ ' + str(e))

    async def reset_command(self, message: IMessage) -> None:
        group_id = self.db.getGroup(message.getChatId()).id
        spendings = self.db.getSpendings(group_id)
        users = spendings_handler.getUsersFromSpendings(spendings) # [Think] get Users From current session, not a list of spendings
        if not users:
            self.db.removeCosts(message.getChatId())
        else:
            await message.reply_text(users, reply_markup=getResetMarkup())

    async def cancel_callback(self, message: IMessage) -> None:
        # rewrite
        query = message.getCallbackQUery()
        chat = query.message.chat.id
        message = query.message.message_id
        cost = self.db.getCost(chat, message)
        if query.from_user.username == cost.telegramFromId:
            self.db.removeCost(chat, message)
            await query.message.delete()
        await query.answer()

    async def reset_callback(self, message: IMessage) -> None:
        # rewrite
        query = message.getCallbackQUery()
        fromUser = query.from_user.username
        chat = query.message.chat.id
        message = query.message.text
        users = message.split(",")
        await query.answer()
        users.remove(fromUser)
        if not users:
            self.db.removeCosts(chat)
            await query.message.edit_text("Траты сброшены💨")
            return
        users = ",".join(users)
        await query.message.edit_text(users, reply_markup=getResetMarkup())
