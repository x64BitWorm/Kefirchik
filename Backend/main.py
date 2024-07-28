import logging
import os
import commands
import database

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def main() -> None:
    """Start the bot."""
    database.initDatabase()
    TOKEN = os.environ.get('TG_TOKEN')
    MODE = os.environ.get('MODE')
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("add", commands.add_command))
    application.add_handler(CommandHandler("report", commands.report_command))
    application.add_handler(CommandHandler("reset", commands.reset_command))
    application.add_handler(CallbackQueryHandler(commands.report_csv_callback, pattern='report-csv'))
    application.add_handler(MessageHandler(filters.REPLY, commands.reply))
    if MODE == 'release':
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

if __name__ == "__main__":
    main()
