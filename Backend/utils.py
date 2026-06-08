from datetime import datetime
import re
from zoneinfo import ZoneInfo

class BotException(Exception):
    def __init__(self, *args):
        super().__init__(*args)
        self.text = args[0]
    
    def __str__(self):
        return self.text

class BotWrongInputException(Exception):
    def __init__(self, *args):
        super().__init__(*args)
        self.text = args[0]
    
    def __str__(self):
        return self.text

def iso_date():
    return datetime.now().replace(microsecond=0).isoformat()

def timestamp_to_datestr(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, ZoneInfo('Europe/Moscow')).strftime('%d.%m.%Y %H:%M')

def unify_whitespace_symbols(s: str):
    """Replace \\t and 0xA0 with a regular space."""
    return re.sub(r'[\t\xA0]', ' ', s)

def normalize_username(username: str | None) -> str:
    return (username or '').casefold()

def usernames_equal(left: str | None, right: str | None) -> bool:
    return normalize_username(left) == normalize_username(right)

def find_username(usernames, target: str) -> str | None:
    return next((username for username in usernames if usernames_equal(username, target)), None)
