import bisect
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

def get_continuation_prefix(text: str) -> str | None:
    for prefix in ('...', '…'):
        if text.startswith(prefix):
            return prefix
    return None

def bisect_index_of(a_list, element):
    idx = bisect.bisect_left(a_list, element)
    if idx < len(a_list) and a_list[idx] == element:
        return idx
    return -1

def bisect_insert_uniq(a_list: list, element):
    idx = bisect.bisect_left(a_list, element)
    if idx < len(a_list) and a_list[idx] == element:
        return
    a_list.insert(idx, element)

def align_tables(*tables: list[list[str]]) -> list[list[str]]:
    tables = [table for table in tables if table]
    if not tables:
        return []
    result = []
    tableWidths = []
    tableHeights = []
    for table in tables:
        tableWidths.append(max(len(row) for row in table) + 1)
        tableHeights.append(len(table))
    totalHeights = max(tableHeights)
    for rowIdx in range(totalHeights):
        row = []
        for tableIdx, table in enumerate(tables):
            tableRow = []
            if len(table) > rowIdx:
                tableRow = table[rowIdx]
            if len(tableRow) < tableWidths[tableIdx]:
                tableRow += [''] * (tableWidths[tableIdx] - len(tableRow))
            row += tableRow
        result.append(row)
    return result
