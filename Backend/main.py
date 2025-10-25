import logging
from config import Config
from tg_wrapper import TgWrapper
from database import DbManager

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def main() -> None:
    """Start the bot."""
    config = Config()
    dbManager = DbManager(config.DB_PATH)
    dbManager.applyMigrations()
    tg_wrapper = TgWrapper(config, dbManager)
    tg_wrapper.startup()

if __name__ == "__main__":
    main()
