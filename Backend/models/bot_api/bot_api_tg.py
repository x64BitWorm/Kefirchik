from aiogram.types import Message, CallbackQuery
from aiogram.types.reaction_type_emoji import ReactionTypeEmoji
from models.bot_api.bot_api_interfaces import IMessage, ICallback


class TgMessage(IMessage):
    _bot = None

    @classmethod
    def set_bot(cls, bot):
        cls._bot = bot

    def __init__(self, msgObj: Message | CallbackQuery):
        self.msgObj = msgObj

    @property
    def _message(self) -> Message:
        if isinstance(self.msgObj, CallbackQuery):
            return self.msgObj.message
        return self.msgObj

    def getChatId(self) -> int:
        return self._message.chat.id

    def getMessageId(self) -> int:
        return self._message.message_id

    def getUsername(self) -> str:
        user = self._message.from_user
        return user.username if user else None

    def getText(self) -> str:
        return self._message.text

    def getCaption(self) -> str:
        return self._message.caption

    def isPhoto(self) -> bool:
        return bool(self._message.photo)

    def getReplyMessageId(self) -> int | None:
        reply = self._message.reply_to_message
        if reply is None:
            return None
        if self._message.is_topic_message and reply.message_id == self._message.message_thread_id:
            return None
        return reply.message_id

    def getReplyMessage(self) -> IMessage:
        return TgMessage(self._message.reply_to_message)

    def getCallbackQuery(self) -> ICallback:
        if isinstance(self.msgObj, CallbackQuery):
            return TgCallback(self.msgObj)
        raise RuntimeError("Not a callback query")

    async def reply_text(self, message: str, reply_markup=None, reply_to_message_id=None, parse_mode=None, disable_web_page_preview=None) -> int:
        kwargs = dict(
            text=message,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
        )
        if reply_to_message_id is not None:
            msg = await self._message.answer(**kwargs, reply_to_message_id=reply_to_message_id)
        else:
            msg = await self._message.reply(**kwargs)
        return msg.message_id

    async def edit_text(self, message: str, reply_markup=None):
        await self._message.edit_text(text=message, reply_markup=reply_markup)

    async def set_reaction(self, reaction: str):
        if self._bot is not None:
            await self._bot.set_message_reaction(
                chat_id=self.getChatId(),
                message_id=self.getMessageId(),
                reaction=[ReactionTypeEmoji(emoji=reaction)],
            )

    async def reply_document(self, document: any, caption: str):
        await self._message.reply_document(document=document, caption=caption)

    async def delete(self):
        await self._message.delete()


class TgCallback(ICallback):
    def __init__(self, cbObj: CallbackQuery):
        self.msgObj = cbObj

    def getData(self) -> str:
        return self.msgObj.data

    def getUsername(self) -> str:
        user = self.msgObj.from_user
        return user.username if user else None

    def getMessage(self) -> IMessage:
        return TgMessage(self.msgObj)

    async def answer(self):
        await self.msgObj.answer()
