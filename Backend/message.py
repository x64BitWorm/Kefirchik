class IMessage:
    def getChatId(self) -> int:
        pass

    def getUsername(self) -> str:
        pass

    def getText(self) -> str:
        pass

    async def reply_text(self, message: str, markup = None) -> int:
        pass

    async def set_reaction(self, reaction):
        pass

class TgMessage(IMessage):
    def __init__(self, msgObj: any):
        self.msgObj = msgObj
        self.chat_id = msgObj.message.chat_id
        self.text = msgObj.message.text
        self.username = msgObj.message.from_user.username
        pass

    def getChatId(self) -> int:
        return self.chat_id
    
    def getUsername(self) -> str:
        return self.username

    def getText(self) -> str:
        return self.text

    async def reply_text(self, message: str, markup = None) -> int:
        return (await self.msgObj.message.reply_text(message, reply_markup=markup)).id

    async def set_reaction(self, reaction):
        await self.msgObj.message.set_reaction(reaction)
