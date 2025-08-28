from services.telegram_markups import getCancelMarkup
import services.parsers as parsers
from handlers.help_handler import *
import handlers.spendings_handler as spendings_handler
from models.bot_api.bot_api_interfaces import IMessage
from database import IDatabase

class ImagesFacade:
    def __init__(self, db: IDatabase):
        self.db = db
    
    async def process_image(self, message: IMessage) -> None:
        data = parsers.ParsedQuery(message.getCaption(), message.getUsername())
        reply_text = spendings_handler.getReplyText(data)
        spendingCompleted = spendings_handler.isSpendingCompleted(data.debtors)
        debtors = spendings_handler.getDebtorsWithAmounts(data.debtors, data.amount) if spendingCompleted else data.debtors
        reply_message_id = await message.reply_text(reply_text, reply_markup=getCancelMarkup())
        self.db.insertCost(reply_message_id, message.getChatId(), spendingCompleted, message.getUsername(), data.amount, debtors, data.comment)
