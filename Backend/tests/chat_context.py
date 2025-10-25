from collections import deque
import random
from database import DbManager
from models.bot_api.bot_api_interfaces import IMessage

class QueueMsgType:
    def __init__(self, type: str, args: list[str]):
        self.type = type
        self.args = args

class ChatContext:
    def __init__(self, db: DbManager):
        self.db = db
        self.msgQueue: deque[QueueMsgType] = deque()
        self.messages: dict[int, IMessage] = dict()
        self.chat_id = random.randint(100, 999)
        self.last_msg_id = 1
    
    def createChat(self):
        dbs = self.db.newSession()
        dbs.getGroup(self.chat_id)
        dbs.close()
