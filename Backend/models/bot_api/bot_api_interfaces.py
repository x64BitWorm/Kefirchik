from __future__ import annotations

class IMessage:
    def getChatId(self) -> int:
        pass

    def getMessageId(self) -> int:
        pass

    def getUsername(self) -> str:
        pass

    def getText(self) -> str:
        pass

    def getReplyMessageId(self) -> int:
        pass

    def getCallbackQuery(self) -> ICallback:
        pass

    async def reply_text(self, message: str, reply_markup = None, reply_to_message_id = None) -> int:
        pass

    async def edit_text(self, message: str, reply_markup = None):
        pass

    async def set_reaction(self, reaction: str):
        pass

    async def reply_document(self, document: any, caption: str):
        pass

    async def delete(self):
        pass


class ICallback:
    def getData(self) -> str:
        pass

    def getUsername(self) -> str:
        pass

    def getMessage(self) -> IMessage:
        pass

    async def answer(self):
        pass
