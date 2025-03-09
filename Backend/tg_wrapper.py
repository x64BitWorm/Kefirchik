from config import Config
from database import IDatabase
from message import TgMessage
from handlers_facade import HandlersFacade
from telegram import ForceReply, Update, constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext
from utils import BotException

def wrap(func):
    async def wrap_internal(update, context):
        message = TgMessage(update)
        try:
            await func(message)
        except BotException as e:
            await message.reply_text(str(e))
        except:
            await message.set_reaction(constants.ReactionEmoji.CRYING_FACE)
    return wrap_internal

class TgWrapper:
    def __init__(self, config: Config, db: IDatabase):
        self.config = config
        self.db = db
        self.handlerFacade = HandlersFacade(db)

    def startup(self):
        application = Application.builder().token(self.config.TOKEN).build()
        application.add_handler(CommandHandler("start", wrap(self.handlerFacade.start_command)))
        application.add_handler(CommandHandler("add", wrap(self.handlerFacade.add_command)))
        #application.add_handler(CommandHandler("report", commands.report_command))
        #application.add_handler(CommandHandler("reset", commands.reset_command))
        #application.add_handler(CallbackQueryHandler(commands.report_csv_callback, pattern='report-csv'))
        #application.add_handler(CallbackQueryHandler(commands.cancel_callback, pattern='cancel-send'))
        #application.add_handler(CallbackQueryHandler(commands.reset_callback, pattern='reset-costs'))
        #application.add_handler(MessageHandler(filters.REPLY, commands.reply))
        if self.config.USE_WEB_HOOKS:
            application.bot.set_webhook(url=f"https://kefirchik-bot.tw1.ru:8443", allowed_updates=Update.ALL_TYPES)
            application.run_webhook(
                listen='0.0.0.0',
                port=8443,
                secret_token='ASecretTokenIHaveChangedByNow',
                key='/var/lib/kefirchik/private.key',
                cert='/var/lib/kefirchik/cert.pem',
                webhook_url='https://kefirchik-bot.tw1.ru:8443'
        )
        else:
            application.run_polling(allowed_updates=Update.ALL_TYPES)
