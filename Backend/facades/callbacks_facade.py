from services.telegram_markups import getResetMarkup
from handlers import reports_handler
from database import IDatabase
from models.bot_api.bot_api_interfaces import IMessage

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
        users = messageText.split(",")
        await query.answer()
        users.remove(fromUser)
        if not users:
            self.db.removeCosts(chatId)
            await message.edit_text("Траты сброшены💨")
            return
        users = ",".join(users)
        await message.edit_text(users, reply_markup=getResetMarkup())
