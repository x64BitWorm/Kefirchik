from chat_context import ChatContext
from bot_api_models import TestMessage
from database import Database
from facades.callbacks_facade import CallbacksFacade
from facades.handlers_facade import HandlersFacade

class ChatEmu:
    def __init__(self):
        self.db = Database()
        self.ctx = ChatContext()
        self.handlerFacade = HandlersFacade(self.db)
        self.callbackFacade = CallbacksFacade(self.db)

    async def sendMessage(self, user: str, text: str, reply_id: int = None):
        msg = TestMessage(self.ctx, user, text, reply_id)
        self.ctx.messages[msg.message_id] = msg
        self.ctx.last_msg_id += 1
        if reply_id == None:
            command = text.split()[0]
            if command == '/start':
                await self.handlerFacade.start_command(msg)
            elif command == '/add':
                await self.handlerFacade.add_command(msg)
            elif command == '/report':
                await self.handlerFacade.report_command(msg)
            elif command == '/reset':
                await self.handlerFacade.reset_command(msg)
        else:
            await self.handlerFacade.reply_command(msg)

    async def pressButton(self, user: str, callbackData: str, msg_id: int):
        msg = TestMessage(self.ctx, user, self.ctx.messages[msg_id].getText(), callback_data=callbackData, message_id=msg_id, reply_id=self.ctx.messages[msg_id].getReplyMessageId())
        if callbackData == 'report-csv':
            await self.callbackFacade.report_csv_callback(msg)
        elif callbackData == 'cancel-send':
            await self.callbackFacade.cancel_callback(msg)
        elif callbackData == 'reset-costs':
            await self.callbackFacade.reset_callback(msg)
        elif callbackData.startswith('last-debtor-approve'):
            await self.callbackFacade.last_debtor_approve_callback(msg)
        

    def getRepliedText(self) -> str | None:
        reply = self.ctx.msgQueue.popleft()
        if reply.type != 'reply_text':
            return None
        return reply.args[0]

    def getEditedText(self) -> str | None:
        reply = self.ctx.msgQueue.popleft()
        if reply.type != 'edit_text':
            return None
        return reply.args[0]

    def getReaction(self) -> str | None:
        reply = self.ctx.msgQueue.popleft()
        if reply.type != 'set_reaction':
            return None
        return reply.args[0]

    def getRepliedDocument(self) -> any:
        reply = self.ctx.msgQueue.popleft()
        if reply.type != 'reply_document':
            return None
        return reply.args[0]

    def messageDeleted(self) -> bool:
        reply = self.ctx.msgQueue.popleft()
        return reply.type == 'delete'
