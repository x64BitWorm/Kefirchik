from models.dto.spendings_dto import SpendingType
from models.bot_api.bot_api_interfaces import IMessage
from services.constants import textLastDebtorQuestion
from services.telegram_markups import getCancelMarkup, getCsvReportMarkup, getLastDebtorApproveMarkup, getResetMarkup
from handlers import reports_handler, parsers_handler, spendings_handler, help_handler
from telegram import constants
from database import IDbSession
import utils

class HandlersFacade:
    def __init__(self):
        pass

    # Показываем отдельный результат, если доля принята, но баланс не сошелся
    async def replySpendingResult(self, message: IMessage, completed: bool, error: str | None) -> None:
        reaction = constants.ReactionEmoji.THINKING_FACE if error else constants.ReactionEmoji.FIRE if completed else constants.ReactionEmoji.THUMBS_UP
        await message.set_reaction(reaction)
        if error:
            await message.reply_text(f'Принято, но {error.lower()}')

    async def start_command(self, message: IMessage, dbs: IDbSession) -> None:
        text, reply_markup = help_handler.getHelpTextAndMarkup()
        await message.reply_text(text, reply_markup=reply_markup)

    async def add_command(self, message: IMessage, dbs: IDbSession) -> None:
        text = message.getCaption() if message.isPhoto() else message.getText()
        data = parsers_handler.ParsedQuery(text, message.getUsername())
        
        # If no debtors specified, split among all users in the group
        if not data.debtors:
            spendings_handler.addEvenSpendingForUsers(data, dbs.getAllUsers(message.getChatId()))
        
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
        if utils.usernames_equal(spending.telegramFromId, message.getUsername()):
            try:
                spendings_handler.getExpressionOfReply(message.getText(), message.getUsername(), spending)
            except Exception:
                isDirectCompletion = False
        debtors = spending.debtors

        # это прямое дополнение траты
        if isDirectCompletion:
            if spending.isCompleted:
                await message.set_reaction(constants.ReactionEmoji.SEE_NO_EVIL_MONKEY)
                return
            expression = spendings_handler.getExpressionOfReply(message.getText(), message.getUsername(), spending)
            debtorKey = utils.find_username(debtors.keys(), message.getUsername()) or message.getUsername()
            debtors[debtorKey] = expression
            result = spendings_handler.tryCompleteSpending(debtors, spending.costAmount)
            dbs.updateSpending(group_id, message.getReplyMessageId(), result.completed, result.debtors, spending.desc)
            await self.replySpendingResult(message, result.completed, result.error)
            metaInfo = spendings_handler.getSpendingMetaInfo(spending)
            if not result.completed and len(metaInfo.notFilledUsers) == 1 and metaInfo.type == SpendingType.SIMPLE:
                replyMessage = message.getReplyMessage()
                replyMessageText = textLastDebtorQuestion(metaInfo.notFilledUsers[0], metaInfo.remainingAmount)
                await replyMessage.reply_text(replyMessageText, reply_markup=getLastDebtorApproveMarkup())
        # это обновление коммента либо дозаполнение траты папиком
        else:
            parsedRefilling = parsers_handler.parseSpendingBody(spending.telegramFromId, message.getText())
            for debtor, debt in parsedRefilling.debtors.items():
                debtorKey = utils.find_username(debtors.keys(), debtor)
                if debtorKey in spendings_handler.getUnfilledUsers(debtors):
                    debtors[debtorKey] = debt
            result = spendings_handler.tryCompleteSpending(debtors, spending.costAmount)
            dbs.updateSpending(group_id, message.getReplyMessageId(), result.completed, result.debtors, parsedRefilling.comment)
            if parsedRefilling.debtors:
                await self.replySpendingResult(message, result.completed, result.error)
            else:
                await message.set_reaction(constants.ReactionEmoji.WRITING_HAND)
            metaInfo = spendings_handler.getSpendingMetaInfo(spending)
            if not result.completed and len(metaInfo.notFilledUsers) == 1 and metaInfo.type == SpendingType.SIMPLE:
                replyMessage = message.getReplyMessage()
                replyMessageText = textLastDebtorQuestion(metaInfo.notFilledUsers[0], metaInfo.remainingAmount)
                await replyMessage.reply_text(replyMessageText, reply_markup=getLastDebtorApproveMarkup())
        dbs.commit()


    async def report_command(self, message: IMessage, dbs: IDbSession) -> None:
        group = dbs.getGroup(message.getChatId())
        spendings = dbs.getSpendings(group.id)

        # Отчет по трате
        replyMessageId = message.getReplyMessageId()
        if replyMessageId != None:
            spending = dbs.getSpending(group.id, replyMessageId)
            if spending == None:
                await message.reply_text('🤓 Для получения отчета по трате, отвечайте на сообщение от бота с текстом "Запомнил..."')
                return
            report_text = reports_handler.getSpendingReport(spending)
            await message.reply_text(report_text)
            return

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
