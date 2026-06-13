import asyncio
import contextlib
import logging
import time
from handlers import help_handler
from facades.callbacks_facade import CallbacksFacade
from config import Config
from database import DbManager
from models.bot_api.bot_api_tg import TgMessage
from facades.handlers_facade import HandlersFacade
from telegram import Update, constants
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ExtBot, MessageHandler, filters
from telegram.error import NetworkError, TimedOut
from telegram.request import HTTPXRequest
from utils import BotException, BotWrongInputException

logger = logging.getLogger(__name__)

POLLING_WATCHDOG_TIMEOUT = 90


class PollingTracker:
    def __init__(self):
        self.last_success = time.monotonic()


class TrackedExtBot(ExtBot):
    __slots__ = ("polling_tracker",)

    def __init__(self, *args, polling_tracker: PollingTracker, **kwargs):
        super().__init__(*args, **kwargs)
        object.__setattr__(self, "polling_tracker", polling_tracker)

    async def get_updates(self, *args, **kwargs):
        updates = await super().get_updates(*args, **kwargs)
        self.polling_tracker.last_success = time.monotonic()
        return updates


class TgWrapper:
    def __init__(self, config: Config, db: DbManager):
        self.config = config
        self.db = db
        self.handlerFacade = HandlersFacade()
        self.callbackFacade = CallbacksFacade()
        self.pollingTracker = PollingTracker()
        self.pollingWatchdogTask = None
        self.pollingStalled = False

    def startup(self):
        if self.config.USE_WEB_HOOKS:
            applicationBuilder = Application.builder().token(self.config.TOKEN)
            if self.config.PROXY_URL != None:
                applicationBuilder = applicationBuilder.proxy(self.config.PROXY_URL)
        else:
            request = HTTPXRequest(proxy=self.config.PROXY_URL)
            getUpdatesRequest = HTTPXRequest(connection_pool_size=1, proxy=self.config.PROXY_URL)
            bot = TrackedExtBot(
                token=self.config.TOKEN,
                request=request,
                get_updates_request=getUpdatesRequest,
                polling_tracker=self.pollingTracker,
            )
            applicationBuilder = (
                Application.builder()
                .bot(bot)
                .post_init(self._start_polling_watchdog)
                .post_shutdown(self._stop_polling_watchdog)
            )
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
            logger.info("Starting Telegram polling with watchdog")
            application.run_polling(allowed_updates=Update.ALL_TYPES, bootstrap_retries=-1)
            if self.pollingStalled:
                raise RuntimeError("Telegram polling watchdog stopped the application")

    async def _error_handler(self, update: Update, context):
        error = context.error
        exceptionInfo = (type(error), error, error.__traceback__)
        if isinstance(context.error, (NetworkError, TimedOut)):
            logger.warning("Telegram network error", exc_info=exceptionInfo)
        else:
            logger.error("Unhandled Telegram error", exc_info=exceptionInfo)

    async def _start_polling_watchdog(self, application):
        self.pollingTracker.last_success = time.monotonic()
        self.pollingWatchdogTask = asyncio.create_task(
            self._polling_watchdog(application),
            name="telegram-polling-watchdog",
        )

    async def _stop_polling_watchdog(self, application):
        if self.pollingWatchdogTask == None:
            return
        self.pollingWatchdogTask.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self.pollingWatchdogTask

    async def _polling_watchdog(self, application):
        while True:
            await asyncio.sleep(10)
            stalledFor = time.monotonic() - self.pollingTracker.last_success
            if stalledFor <= POLLING_WATCHDOG_TIMEOUT:
                continue
            logger.critical(
                "Telegram polling stalled for %.0f seconds; terminating for Docker restart",
                stalledFor,
            )
            self.pollingStalled = True
            application.stop_running()
            return

    def wrap(self, func):
        async def wrap_internal(update: Update, context):
            logger.info(
                "Telegram handler started: handler=%s, update_id=%s",
                func.__name__,
                update.update_id,
            )
            message = TgMessage(update)
            session = self.db.newSession()
            try:
                await func(message, session)
            except BotException as e:
                await message.reply_text(str(e))
            except BotWrongInputException as e:
                text = f"❌ {e.text}\n<a href=\"{help_handler.getInstructionLink()}\">Как исправить?</a>"
                await message.reply_text(text, parse_mode='HTML', disable_web_page_preview=True)
            except Exception:
                logger.exception(
                    "Telegram handler failed: handler=%s, update_id=%s",
                    func.__name__,
                    update.update_id,
                )
                with contextlib.suppress(Exception):
                    await message.set_reaction(constants.ReactionEmoji.CRYING_FACE)
                if not self.config.IS_PROD:
                    raise
            finally:
                session.close()
                logger.info(
                    "Telegram handler finished: handler=%s, update_id=%s",
                    func.__name__,
                    update.update_id,
                )
        return wrap_internal
