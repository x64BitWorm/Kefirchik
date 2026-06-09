import sys
import time
from handlers import help_handler
from facades.callbacks_facade import CallbacksFacade
from config import Config
from database import DbManager
from models.bot_api.bot_api_tg import TgMessage
from facades.handlers_facade import HandlersFacade
from telegram import Update, constants
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.error import NetworkError, TimedOut
from utils import BotException, BotWrongInputException

class TgWrapper:
    def __init__(self, config: Config, db: DbManager):
        self.config = config
        self.db = db
        self.handlerFacade = HandlersFacade()
        self.callbackFacade = CallbacksFacade()

    def startup(self):
        """Auto restars updater on fail"""
        while True:
            try:
                self._run_bot()
            except (NetworkError, TimedOut) as e:
                print(f"Network error: {e}. Restart in 15 seconds...", file=sys.stderr)
            except Exception as e:
                print(f"Critical error: {e}. Restart in 15 seconds...", file=sys.stderr)
            finally:
                time.sleep(15)

    def _run_bot(self):
        applicationBuilder = Application.builder().token(self.config.TOKEN)
        if self.config.PROXY_URL != None:
            applicationBuilder = applicationBuilder.proxy(self.config.PROXY_URL).get_updates_proxy(self.config.PROXY_URL)
        application = applicationBuilder.build()
        application.add_error_handler(self._error_handler)
        
        application.add_handler(CommandHandler("start", self.wrap(self.handlerFacade.start_command)))
        application.add_handler(CommandHandler("add", self.wrap(self.handlerFacade.add_command)))
        application.add_handler(CommandHandler("report", self.wrap(self.handlerFacade.report_command)))
        application.add_handler(CommandHandler("reset", self.wrap(self.handlerFacade.reset_command)))
        application.add_handler(MessageHandler(filters.REPLY, self.wrap(self.handlerFacade.reply_command)))
        application.add_handler(MessageHandler(filters.PHOTO & filters.CaptionRegex('^/add'), self.wrap(self.handlerFacade.add_command)))
        application.add_handler(CallbackQueryHandler(self.wrap(self.callbackFacade.report_csv_callback), pattern='report-csv'))
        application.add_handler(CallbackQueryHandler(self.wrap(self.callbackFacade.cancel_callback), pattern='cancel-send'))
        application.add_handler(CallbackQueryHandler(self.wrap(self.callbackFacade.reset_callback), pattern='reset-costs'))
        application.add_handler(CallbackQueryHandler(self.wrap(self.callbackFacade.last_debtor_approve_callback), pattern='last-debtor-approve'))
        
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
            try:
                application.run_polling(allowed_updates=Update.ALL_TYPES)
            except (NetworkError, TimedOut) as e:
                print(f"Polling error: {e}", file=sys.stderr)
                raise

    async def _error_handler(self, update: Update, context):
        if isinstance(context.error, (NetworkError, TimedOut)):
            print(f"Network error: {context.error}", file=sys.stderr)
        else:
            print(f"Critical error: {context.error}", file=sys.stderr)

    def wrap(self, func):
        async def wrap_internal(update: Update, context):
            message = TgMessage(update)
            session = self.db.newSession()
            try:
                await func(message, session)
            except BotException as e:
                await message.reply_text(str(e))
            except BotWrongInputException as e:
                text = f"❌ {e.text}\n<a href=\"{help_handler.getInstructionLink()}\">Как исправить?</a>"
                await message.reply_text(text, parse_mode='HTML', disable_web_page_preview=True)
            except Exception as e:
                await message.set_reaction(constants.ReactionEmoji.CRYING_FACE)
                if not self.config.IS_PROD:
                    raise e
            finally:
                session.close()
        return wrap_internal
