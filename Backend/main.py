import logging
import os
import commands
import database

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def main() -> None:
    """Start the bot."""
    database.initDatabase()
    TOKEN = os.environ.get('TG_TOKEN')
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("add", commands.add_command))
    application.add_handler(CommandHandler("report", commands.report_command))
    application.add_handler(CommandHandler("reset", commands.reset_command))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
