from models.bot_api.bot_api_interfaces import IMessage, ICallback

class TgMessage(IMessage):
    def __init__(self, msgObj: any):
        self.msgObj = msgObj

    def getChatId(self) -> int:
        return self.msgObj.message.chat_id
    
    def getMessageId(self) -> int:
        return self.msgObj.message.message_id
    
    def getUsername(self) -> str:
        return self.msgObj.message.from_user.username

    def getText(self) -> str:
        return self.msgObj.message.text
    
    def getReplyMessageId(self) -> int:
        return self.msgObj.message.reply_to_message.id
    
    def getCallbackQuery(self) -> ICallback:
        return TgCallback(self.msgObj.callback_query)

    async def reply_text(self, message: str, reply_markup = None, reply_to_message_id = None) -> int:
        return (await self.msgObj.message.reply_text(message, reply_markup=reply_markup, reply_to_message_id=reply_to_message_id)).id
    
    async def edit_text(self, message: str, reply_markup = None):
        await self.msgObj.message.edit_text(message, reply_markup=reply_markup)
    
    async def set_reaction(self, reaction: str):
        await self.msgObj.message.set_reaction(reaction)
    
    async def reply_document(self, document: any, caption: str):
        await self.msgObj.message.reply_document(document=document, caption=caption)
    
    async def delete(self):
        await self.msgObj.message.delete()


class TgCallback(ICallback):
    def __init__(self, cbObj: any):
        self.msgObj = cbObj
        self.data = cbObj.data
        self.message = cbObj.message
        self.username = cbObj.from_user.username

    def getData(self) -> str:
        return self.data

    def getUsername(self) -> str:
        return self.username
    
    def getMessage(self) -> IMessage:
        return TgMessage(self.msgObj)
    
    async def answer(self):
        await self.msgObj.answer()
