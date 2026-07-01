import asyncio
import contextlib
import logging
import re
import ssl
from handlers import help_handler
from facades.callbacks_facade import CallbacksFacade
from config import Config
from database import DbManager
from models.bot_api.bot_api_tg import TgMessage
from models.bot_api.reactions import ReactionEmoji
from facades.handlers_facade import HandlersFacade
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, ErrorEvent
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramNetworkError
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from utils import BotException, BotWrongInputException

logger = logging.getLogger(__name__)


def _photo_with_add_command(message: Message) -> bool:
    return bool(message.photo and message.caption and re.match(r"^/add(?:@\w+)?(?:\s|$)", message.caption))


class TgWrapper:
    def __init__(self, config: Config, db: DbManager):
        self.config = config
        self.db = db
        self.handlerFacade = HandlersFacade()
        self.callbackFacade = CallbacksFacade()

        session = None
        if config.PROXY_URL:
            session = AiohttpSession(proxy=config.PROXY_URL)

        self.bot = Bot(
            token=config.TOKEN,
            session=session,
            default=DefaultBotProperties(),
        )
        self.dp = Dispatcher()
        TgMessage.set_bot(self.bot)
        self._register_handlers()

    def _register_handlers(self):
        self.dp.message.register(self._wrap_message(self.handlerFacade.start_command), Command("start"))
        self.dp.message.register(self._wrap_message(self.handlerFacade.add_command), Command("add"))
        self.dp.message.register(self._wrap_message(self.handlerFacade.report_command), Command("report"))
        self.dp.message.register(self._wrap_message(self.handlerFacade.reset_command), Command("reset"))
        self.dp.message.register(self._wrap_message(self.handlerFacade.reply_command), F.reply_to_message)
        self.dp.message.register(self._wrap_message(self.handlerFacade.add_command), _photo_with_add_command)

        self.dp.callback_query.register(self._wrap_callback(self.callbackFacade.report_csv_callback), F.data == 'report-csv')
        self.dp.callback_query.register(self._wrap_callback(self.callbackFacade.cancel_callback), F.data == 'cancel-send')
        self.dp.callback_query.register(self._wrap_callback(self.callbackFacade.reset_callback), F.data == 'reset-costs')
        self.dp.callback_query.register(self._wrap_callback(self.callbackFacade.last_debtor_approve_callback), F.data.startswith('last-debtor-approve'))

        self.dp.errors.register(self._error_handler)

    async def _error_handler(self, event: ErrorEvent, **kwargs):
        error = event.exception
        exceptionInfo = (type(error), error, error.__traceback__)
        if isinstance(error, TelegramNetworkError):
            logger.warning("Telegram network error", exc_info=exceptionInfo)
        else:
            logger.error("Unhandled Telegram error", exc_info=exceptionInfo)

    def startup(self):
        if self.config.USE_WEB_HOOKS:
            asyncio.run(self._start_webhook())
        else:
            logger.info("Starting Telegram polling")
            asyncio.run(self._start_polling())

    async def _start_polling(self):
        try:
            await self.bot.delete_webhook(drop_pending_updates=False)
            await self.dp.start_polling(self.bot, allowed_updates=self.dp.resolve_used_update_types())
        finally:
            await self.bot.session.close()

    async def _start_webhook(self):
        try:
            await self.bot.set_webhook(
                url="https://kefirchik-bot.tw1.ru:8443/webhook",
                secret_token='ASecretTokenIHaveChangedByNow',
                allowed_updates=self.dp.resolve_used_update_types(),
            )
            app = web.Application()
            webhook_requests_handler = SimpleRequestHandler(
                dispatcher=self.dp,
                bot=self.bot,
                secret_token='ASecretTokenIHaveChangedByNow',
            )
            webhook_requests_handler.register(app, path='/webhook')
            setup_application(app, self.dp, bot=self.bot)

            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(
                certfile='/var/lib/kefirchik/cert.pem',
                keyfile='/var/lib/kefirchik/private.key',
            )

            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', 8443, ssl_context=ssl_context)
            await site.start()

            await asyncio.Event().wait()
        finally:
            await self.bot.session.close()

    def _wrap_message(self, func):
        async def wrapper(message: Message):
            logger.info(
                "Telegram handler started: handler=%s, message_id=%s",
                func.__name__,
                message.message_id,
            )
            tg_message = TgMessage(message)
            session = self.db.newSession()
            try:
                await func(tg_message, session)
            except BotException as e:
                await tg_message.reply_text(str(e))
            except BotWrongInputException as e:
                text = f"❌ {e.text}\n<a href=\"{help_handler.getInstructionLink()}\">Как исправить?</a>"
                await tg_message.reply_text(text, parse_mode='HTML', disable_web_page_preview=True)
            except Exception:
                logger.exception(
                    "Telegram handler failed: handler=%s, message_id=%s",
                    func.__name__,
                    message.message_id,
                )
                with contextlib.suppress(Exception):
                    await tg_message.set_reaction(ReactionEmoji.CRYING_FACE)
                if not self.config.IS_PROD:
                    raise
            finally:
                session.close()
                logger.info(
                    "Telegram handler finished: handler=%s, message_id=%s",
                    func.__name__,
                    message.message_id,
                )
        return wrapper

    def _wrap_callback(self, func):
        async def wrapper(callback: CallbackQuery):
            logger.info(
                "Telegram callback handler started: handler=%s, data=%s",
                func.__name__,
                callback.data,
            )
            tg_message = TgMessage(callback)
            session = self.db.newSession()
            try:
                await func(tg_message, session)
            except BotException as e:
                await tg_message.reply_text(str(e))
            except BotWrongInputException as e:
                text = f"❌ {e.text}\n<a href=\"{help_handler.getInstructionLink()}\">Как исправить?</a>"
                await tg_message.reply_text(text, parse_mode='HTML', disable_web_page_preview=True)
            except Exception:
                logger.exception(
                    "Telegram callback handler failed: handler=%s, data=%s",
                    func.__name__,
                    callback.data,
                )
                with contextlib.suppress(Exception):
                    await tg_message.set_reaction(ReactionEmoji.CRYING_FACE)
                if not self.config.IS_PROD:
                    raise
            finally:
                session.close()
                logger.info(
                    "Telegram callback handler finished: handler=%s, data=%s",
                    func.__name__,
                    callback.data,
                )
        return wrapper
