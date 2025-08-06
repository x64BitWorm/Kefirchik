import json
from services.constants import textLastDebtorApprove
from models.dto.spendings_dto import SpendingType
from services.telegram_markups import getResetMarkup
from handlers import reports_handler, spendings_handler
from database import IDatabase
from models.bot_api.bot_api_interfaces import IMessage
from telegram import constants

class CallbacksFacade:
    def __init__(self, db: IDatabase):
        self.db = db
    
    async def report_csv_callback(self, message: IMessage) -> None:
        query = message.getCallbackQuery()
        message = query.getMessage()
        group = self.db.getGroup(message.getChatId())
        spendings = self.db.getSpendings(group.id)
        doc = reports_handler.generateCsv(spendings)
        await message.reply_document(document=doc, caption='Ваш отчет готов 📈 @' + query.getUsername())
        await query.answer()

    async def cancel_callback(self, message: IMessage) -> None:
        query = message.getCallbackQuery()
        message = query.getMessage()
        chatId = message.getChatId()
        messageId = message.getMessageId()
        cost = self.db.getCost(chatId, messageId)
        if query.getUsername() == cost.telegramFromId:
            self.db.removeCost(chatId, messageId)
            await message.delete()
        await query.answer()

    async def reset_callback(self, message: IMessage) -> None:
        query = message.getCallbackQuery()
        message = query.getMessage()
        fromUser = query.getUsername()
        chatId = message.getChatId()
        messageText = message.getText()
        users = [u[1:] for u in messageText.split() if u.startswith("@")]
        await query.answer()
        if fromUser not in users:
            return
        users.remove(fromUser)
        if users:
            users = "@" + " @".join(users)
            await message.edit_text(users, reply_markup=getResetMarkup())
        else:
            self.db.removeCosts(chatId)
            await message.edit_text("Траты сброшены💨")

    async def last_debtor_approve_callback(self, message: IMessage) -> None:
        query = message.getCallbackQuery()
        message = query.getMessage()
        chatId = message.getChatId()
        spending = self.db.getCost(chatId, message.getReplyMessageId())
        metaInfo = spendings_handler.getSpendingMetaInfo(spending)
        await query.answer()
        fromUser = query.getUsername()
        if metaInfo.notFilledUsers != [fromUser] or metaInfo.type != SpendingType.SIMPLE:
            return
        group_id = self.db.getGroup(chatId).id
        buttonData = query.getData()
        if buttonData.endswith('/yes'):
            spending.debtors[fromUser] = str(metaInfo.remainingAmount)
            spending.debtors = spendings_handler.getDebtorsWithAmounts(spending.debtors, spending.costAmount)
            self.db.updateCost(group_id, message.getReplyMessageId(), True, spending.debtors, spending.desc)
            await message.set_reaction(constants.ReactionEmoji.FIRE)
            await message.edit_text(textLastDebtorApprove(fromUser, metaInfo.remainingAmount))
        elif buttonData.endswith('/no'):
            await message.delete()
