from datetime import datetime
import pytz

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
    return datetime.fromtimestamp(timestamp, pytz.timezone('Europe/Moscow')).strftime('%d.%m.%Y %H:%M')
