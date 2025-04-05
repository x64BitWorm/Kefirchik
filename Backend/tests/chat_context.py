from collections import deque

class QueueMsgType:
    def __init__(self, type: str, args: list[str]):
        self.type = type
        self.args = args

class ChatContext:
    def __init__(self):
        self.msgQueue: deque[QueueMsgType] = deque()
        self.chat_id = 123
        self.last_msg_id = 1
