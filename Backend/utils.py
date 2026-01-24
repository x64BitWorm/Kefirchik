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

def iso_date():
    return datetime.now().replace(microsecond=0).isoformat()

def timestamp_to_datestr(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, ZoneInfo('Europe/Moscow')).strftime('%d.%m.%Y %H:%M')

def unify_whitespace_symbols(s: str):
    """ Replace \\t, 0xA0 to \s """
    return re.sub(r'[\t\xA0]', ' ', s)
