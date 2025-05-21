from chat_context import ChatContext, QueueMsgType
from models.bot_api.bot_api_interfaces import IMessage, ICallback

class TestMessage(IMessage):
    def __init__(self, ctx: ChatContext, user: str, text: str, reply_id: int = None, 
                 callback_data: str = None, message_id: int  = None):
        self.ctx = ctx
        self.user = user
        self.text = text
        self.reply_id = reply_id
        self.message_id = self.ctx.last_msg_id if message_id == None else message_id
        self.callback_data = callback_data
    
    def __str__(self):
        return f'<Id: {self.message_id}, ReplyId: {self.reply_id}, User: {self.user}, Text: {self.text}>'

    def getChatId(self) -> int:
        return self.ctx.chat_id
    
    def getMessageId(self) -> int:
        return self.message_id
    
    def getUsername(self) -> str:
        return self.user

    def getText(self) -> str:
        return self.text
    
    def getReplyMessageId(self) -> int:
        return self.reply_id
    
    def getReplyMessage(self) -> IMessage:
        return self.ctx.messages[self.reply_id]
    
    def getCallbackQuery(self) -> ICallback:
        return TestCallback(self, self.callback_data)

    async def reply_text(self, message: str, reply_markup = None, reply_to_message_id = None) -> int:
        self.ctx.msgQueue.append(QueueMsgType('reply_text', [message, reply_to_message_id]))
        msg = TestMessage(self.ctx, 'bot', message, self.message_id)
        self.ctx.messages[msg.message_id] = msg
        self.ctx.last_msg_id += 1
        return msg.message_id
    
    async def edit_text(self, message: str, reply_markup = None):
        self.ctx.msgQueue.append(QueueMsgType('edit_text', [message, self.message_id]))
    
    async def set_reaction(self, reaction: str):
        self.ctx.msgQueue.append(QueueMsgType('set_reaction', [reaction]))
    
    async def reply_document(self, document: any, caption: str):
        self.ctx.msgQueue.append(QueueMsgType('reply_document', [document]))
        msg = TestMessage(self.ctx, 'bot', str(document))
        self.ctx.messages[msg.message_id] = msg
        self.ctx.last_msg_id += 1
        return msg.message_id
    
    async def delete(self):
        self.ctx.msgQueue.append(QueueMsgType('delete', [self.message_id]))


class TestCallback(ICallback):
    def __init__(self, msg: IMessage, data: str | None):
        self.msg = msg
        self.data = data

    def getData(self) -> str:
        return self.data

    def getUsername(self) -> str:
        return self.msg.getUsername()
    
    def getMessage(self) -> IMessage:
        return self.msg
    
    async def answer(self):
        pass
