import logging
from config import Config
from tg_wrapper import TgWrapper
from database import Database

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def main() -> None:
    """Start the bot."""
    config = Config()
    db = Database(config.DB_PATH)
    tg_wrapper = TgWrapper(config, db)
    tg_wrapper.startup()

if __name__ == "__main__":
    main()
