from models.dto.spendings_dto import SpendingType
from models.bot_api.bot_api_interfaces import IMessage
from services.constants import textLastDebtorQuestion
from services.telegram_markups import getCancelMarkup, getCsvReportMarkup, getLastDebtorApproveMarkup, getResetMarkup
from handlers import reports_handler, parsers_handler, spendings_handler, help_handler
from telegram import constants
from database import IDbSession

class HandlersFacade:
    def __init__(self):
        pass

    async def start_command(self, message: IMessage, dbs: IDbSession) -> None:
        await message.reply_text(help_handler.getHelpText())

    async def add_command(self, message: IMessage, dbs: IDbSession) -> None:
        text = message.getCaption() if message.isPhoto() else message.getText()
        data = parsers_handler.ParsedQuery(text, message.getUsername())
        reply_text = spendings_handler.getReplyText(data)
        spendingCompleted = spendings_handler.isSpendingCompleted(data.debtors)
        debtors = spendings_handler.getDebtorsWithAmounts(data.debtors, data.amount) if spendingCompleted else data.debtors
        reply_message_id = await message.reply_text(reply_text, reply_markup=getCancelMarkup())
        dbs.insertSpending(reply_message_id, message.getChatId(), spendingCompleted, message.getUsername(), data.amount, debtors, data.comment)
        dbs.commit()

    async def reply_command(self, message: IMessage, dbs: IDbSession) -> None:
        group_id = dbs.getGroup(message.getChatId()).id
        spending = dbs.getSpending(group_id, message.getReplyMessageId())
        if spending is None:
            return
        
        isDirectCompletion = True
        # папик хочет обновить коммент или дозаполнить трату за должников?
        if spending.telegramFromId == message.getUsername():
            try:
                spendings_handler.getExpressionOfReply(message.getText(), message.getUsername(), spending)
            except Exception:
                isDirectCompletion = False
        debtors = spending.debtors

        # это прямое дополнение траты
        if isDirectCompletion:
            if spendings_handler.isSpendingCompleted(debtors):
                await message.set_reaction(constants.ReactionEmoji.SEE_NO_EVIL_MONKEY)
                return
            expression = spendings_handler.getExpressionOfReply(message.getText(), message.getUsername(), spending)
            debtors[message.getUsername()] = expression
            spendingCompleted = spendings_handler.isSpendingCompleted(debtors)
            if spendingCompleted:
                debtors = spendings_handler.getDebtorsWithAmounts(debtors, spending.costAmount) # resolve x's
            dbs.updateSpending(group_id, message.getReplyMessageId(), spendingCompleted, debtors, spending.desc)
            await message.set_reaction(constants.ReactionEmoji.FIRE if spendingCompleted else constants.ReactionEmoji.THUMBS_UP)
            metaInfo = spendings_handler.getSpendingMetaInfo(spending)
            if not spendingCompleted and len(metaInfo.notFilledUsers) == 1 and metaInfo.type == SpendingType.SIMPLE:
                replyMessage = message.getReplyMessage()
                replyMessageText = textLastDebtorQuestion(metaInfo.notFilledUsers[0], metaInfo.remainingAmount)
                await replyMessage.reply_text(replyMessageText, reply_markup=getLastDebtorApproveMarkup())
        # это обновление коммента либо дозаполнение траты папиком
        else:
            parsedRefilling = parsers_handler.parseSpendingBody(spending.telegramFromId, message.getText())
            for debtor, debt in parsedRefilling.debtors.items():
                if debtor in spendings_handler.getUnfilledUsers(debtors):
                    debtors[debtor] = debt
            spendingCompleted = spendings_handler.isSpendingCompleted(debtors)
            if spendingCompleted:
                debtors = spendings_handler.getDebtorsWithAmounts(debtors, spending.costAmount) # resolve x's
            dbs.updateSpending(group_id, message.getReplyMessageId(), spendingCompleted, debtors, parsedRefilling.comment)
            if parsedRefilling.debtors:
                await message.set_reaction(constants.ReactionEmoji.FIRE if spendingCompleted else constants.ReactionEmoji.THUMBS_UP)
            else:
                await message.set_reaction(constants.ReactionEmoji.WRITING_HAND)
            metaInfo = spendings_handler.getSpendingMetaInfo(spending)
            if not spendingCompleted and len(metaInfo.notFilledUsers) == 1 and metaInfo.type == SpendingType.SIMPLE:
                replyMessage = message.getReplyMessage()
                replyMessageText = textLastDebtorQuestion(metaInfo.notFilledUsers[0], metaInfo.remainingAmount)
                await replyMessage.reply_text(replyMessageText, reply_markup=getLastDebtorApproveMarkup())
        dbs.commit()


    async def report_command(self, message: IMessage, dbs: IDbSession) -> None:
        group = dbs.getGroup(message.getChatId())
        spendings = dbs.getSpendings(group.id)

        uncompletedSpending = reports_handler.getUncompletedSpending(spendings)
        warningUncompleted = ''
        reply_to_message_id = None
        if uncompletedSpending != None:
            warningUncompleted = reports_handler.getUncompletedWarningText(uncompletedSpending)
            reply_to_message_id = uncompletedSpending.messageId

        report = reports_handler.getReportInfo(spendings)
        if report.transactions_count > 0:
            await message.reply_text(warningUncompleted + report.text, reply_markup=getCsvReportMarkup(), reply_to_message_id=reply_to_message_id)
        else:
            await message.reply_text(warningUncompleted + report.text, reply_to_message_id=reply_to_message_id)

    async def reset_command(self, message: IMessage, dbs: IDbSession) -> None:
        group_id = dbs.getGroup(message.getChatId()).id
        spendings = dbs.getSpendings(group_id)
        users = spendings_handler.getUsersFromSpendings(spendings) # [Think] get Users From current session, not a list of spendings
        if not users:
            dbs.removeSpendings(message.getChatId())
            dbs.commit()
        else:
            await message.reply_text(users, reply_markup=getResetMarkup())
