import json
from services.constants import textLastDebtorApprove, textLastDebtorPapikApprove
from models.dto.spendings_dto import SpendingType
from services.telegram_markups import getResetMarkup
from handlers import reports_handler, spendings_handler
from database import IDbSession
from models.bot_api.bot_api_interfaces import IMessage
from telegram import constants

class CallbacksFacade:
    def __init__(self):
        pass
    
    async def report_csv_callback(self, message: IMessage, dbs: IDbSession) -> None:
        query = message.getCallbackQuery()
        message = query.getMessage()
        group = dbs.getGroup(message.getChatId())
        spendings = dbs.getSpendings(group.id)
        doc = reports_handler.generateCsv(spendings)
        await message.reply_document(document=doc, caption='Ваш отчет готов 📈 @' + query.getUsername())
        await query.answer()

    async def cancel_callback(self, message: IMessage, dbs: IDbSession) -> None:
        query = message.getCallbackQuery()
        message = query.getMessage()
        chatId = message.getChatId()
        messageId = message.getMessageId()
        cost = dbs.getSpending(chatId, messageId)
        if query.getUsername() == cost.telegramFromId:
            dbs.removeSpending(chatId, messageId)
            dbs.commit()
            await message.delete()
        await query.answer()

    async def reset_callback(self, message: IMessage, dbs: IDbSession) -> None:
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
            dbs.removeSpendings(chatId)
            await message.edit_text("Траты сброшены💨")
        dbs.commit()

    async def last_debtor_approve_callback(self, message: IMessage, dbs: IDbSession) -> None:
        query = message.getCallbackQuery()
        message = query.getMessage()
        chatId = message.getChatId()
        spending = dbs.getSpending(chatId, message.getReplyMessageId())
        metaInfo = spendings_handler.getSpendingMetaInfo(spending)
        await query.answer()
        fromUser = query.getUsername()
        if metaInfo.notFilledUsers != [fromUser] and fromUser != spending.telegramFromId or metaInfo.type != SpendingType.SIMPLE:
            return
        debtors = spending.debtors
        group_id = dbs.getGroup(chatId).id
        buttonData = query.getData()
        if buttonData.endswith('/yes'):
            debtors[metaInfo.notFilledUsers[0]] = str(metaInfo.remainingAmount)
            debtors = spendings_handler.getDebtorsWithAmounts(debtors, spending.costAmount)
            dbs.updateSpending(group_id, message.getReplyMessageId(), True, debtors, spending.desc)
            await message.set_reaction(constants.ReactionEmoji.FIRE)
            if fromUser == metaInfo.notFilledUsers[0]:
                await message.edit_text(textLastDebtorApprove(fromUser, metaInfo.remainingAmount))
            else:
                await message.edit_text(textLastDebtorPapikApprove(fromUser, metaInfo.notFilledUsers[0], metaInfo.remainingAmount))
        elif buttonData.endswith('/no'):
            await message.delete()
        dbs.commit()
