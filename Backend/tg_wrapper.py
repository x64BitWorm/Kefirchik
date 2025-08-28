from facades.images_facade import ImagesFacade
from facades.callbacks_facade import CallbacksFacade
from config import Config
from database import IDatabase
from models.bot_api.bot_api_tg import TgMessage
from facades.handlers_facade import HandlersFacade
from telegram import Update, constants
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from utils import BotException, BotWrongInputException

def wrap(func):
    async def wrap_internal(update: Update, context):
        message = TgMessage(update)
        try:
            await func(message)
        except BotException as e:
            await message.reply_text(str(e))
        except BotWrongInputException as e:
            await message.set_reaction(constants.ReactionEmoji.CLOWN_FACE)
        except:
            await message.set_reaction(constants.ReactionEmoji.CRYING_FACE)
    return wrap_internal

class TgWrapper:
    def __init__(self, config: Config, db: IDatabase):
        self.config = config
        self.db = db
        self.handlerFacade = HandlersFacade(db)
        self.callbackFacade = CallbacksFacade(db)
        self.imagesFacade = ImagesFacade(db)

    def startup(self):
        application = Application.builder().token(self.config.TOKEN).build()
        application.add_handler(CommandHandler("start", wrap(self.handlerFacade.start_command)))
        application.add_handler(CommandHandler("add", wrap(self.handlerFacade.add_command)))
        application.add_handler(CommandHandler("report", wrap(self.handlerFacade.report_command)))
        application.add_handler(CommandHandler("reset", wrap(self.handlerFacade.reset_command)))
        application.add_handler(MessageHandler(filters.REPLY, wrap(self.handlerFacade.reply_command)))
        application.add_handler(MessageHandler(filters.PHOTO, wrap(self.imagesFacade.process_image)))
        application.add_handler(CallbackQueryHandler(wrap(self.callbackFacade.report_csv_callback), pattern='report-csv'))
        application.add_handler(CallbackQueryHandler(wrap(self.callbackFacade.cancel_callback), pattern='cancel-send'))
        application.add_handler(CallbackQueryHandler(wrap(self.callbackFacade.reset_callback), pattern='reset-costs'))
        application.add_handler(CallbackQueryHandler(wrap(self.callbackFacade.last_debtor_approve_callback), pattern='last-debtor-approve'))
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
