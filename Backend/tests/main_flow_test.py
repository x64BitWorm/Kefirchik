from chat_emu import ChatEmu
import unittest
from telegram import constants
import asyncio

class TestSpendings(unittest.IsolatedAsyncioTestCase):

    async def test_add_spending(self):
        emu = ChatEmu()

        await emu.sendMessage('alice', '/add 200.5\n@bob 200.5\ntea')
        self.assertEqual('Запомнил🍶', emu.getRepliedText())
        
        await emu.sendMessage('alice', '/report')
        self.assertEqual('bob ➡️ alice 200.5🎪\n', emu.getRepliedText())

    async def test_reply_spending(self):
        emu = ChatEmu()

        await emu.sendMessage('alice', '/add 200\n@bob 50\n@eve\ntea')
        self.assertEqual('Запомнил🍶 ждем  @eve', emu.getRepliedText())

        await emu.sendMessage('eve', '150', reply_id=2) # Reply to 2 message in chat
        self.assertEqual(constants.ReactionEmoji.FIRE, emu.getReaction())

        await emu.sendMessage('alice', '/report')
        self.assertEqual('eve ➡️ alice 150🎪\nbob ➡️ alice 50🎪\n', emu.getRepliedText())

    async def test_reply_add_debt(self):
        emu = ChatEmu()

        await emu.sendMessage('bob', '/add 500\n@alice 30\n@eve @bob')
        self.assertEqual('Запомнил🍶 ждем  @eve @bob', emu.getRepliedText())

        await emu.sendMessage('eve', '200', reply_id=2)
        self.assertEqual(constants.ReactionEmoji.THUMBS_UP, emu.getReaction())    
        self.assertEqual('@bob должен 270?', emu.getRepliedText()) # игнорим

        await emu.sendMessage('alice', '...+150', reply_id=2)
        self.assertEqual(constants.ReactionEmoji.THUMBS_UP, emu.getReaction())    
        self.assertEqual('@bob должен 120?', emu.getRepliedText()) # игнорим

        await emu.sendMessage('bob', 'x', reply_id=2)
        self.assertEqual(constants.ReactionEmoji.FIRE, emu.getReaction())

        await emu.sendMessage('eve', '/report')
        self.assertEqual('eve ➡️ bob 200🎪\nalice ➡️ bob 180🎪\n', emu.getRepliedText())

    async def test_reply_comment(self):
        emu = ChatEmu()

        await emu.sendMessage('bob', '/add 500\n@alice 300\n@eve')
        self.assertEqual('Запомнил🍶 ждем  @eve', emu.getRepliedText())

        try: await emu.sendMessage('eve', 'borga??', reply_id=2)
        except Exception: pass
        else: self.fail('Expected exception not raised')

        await emu.sendMessage('eve', '200', reply_id=2)
        self.assertEqual(constants.ReactionEmoji.FIRE, emu.getReaction())    

        await emu.sendMessage('bob', 'da eto borga', reply_id=2)
        self.assertEqual(constants.ReactionEmoji.WRITING_HAND, emu.getReaction())

        await emu.sendMessage('eve', '/report')
        self.assertEqual('alice ➡️ bob 300🎪\neve ➡️ bob 200🎪\n', emu.getRepliedText())

    async def test_reply_refilling(self):
        emu = ChatEmu()

        await emu.sendMessage('alice', '/add 1000\n@bob 300\n@eve @alex @john @rob')
        self.assertEqual('Запомнил🍶 ждем  @eve @alex @john @rob', emu.getRepliedText())

        await emu.sendMessage('alice', '@eve @alex 150\n@john 100', reply_id=2)
        self.assertEqual(constants.ReactionEmoji.THUMBS_UP, emu.getReaction())
        self.assertEqual('@rob должен 300?', emu.getRepliedText()) # игнорим

        await emu.sendMessage('alice', '@rob 300\n@bob 400', reply_id=2)
        self.assertEqual(constants.ReactionEmoji.FIRE, emu.getReaction())

        await emu.sendMessage('alice', '/report')
        self.assertEqual('bob ➡️ alice 300🎪\nrob ➡️ alice 300🎪\nalex ➡️ alice 150🎪\neve ➡️ alice 150🎪\njohn ➡️ alice 100🎪\n', emu.getRepliedText())

    async def test_cancel_spending(self):
        emu = ChatEmu()

        await emu.sendMessage('alice', '/add 200\n@я 200\ntea')
        self.assertEqual('Запомнил🍶', emu.getRepliedText())

        await emu.pressButton('alice', 'cancel-send', msg_id=2) # Press button on 2 message in chat
        self.assertTrue(emu.messageDeleted())
        
        await emu.sendMessage('alice', '/report')
        self.assertEqual('⚠️ Нет записанных трат', emu.getRepliedText())
    
    async def test_uncompleted_report(self):
        emu = ChatEmu()

        await emu.sendMessage('bob', '/add 200\n@alice 200\ntea')
        self.assertEqual('Запомнил🍶', emu.getRepliedText())
        
        await emu.sendMessage('alice', '/report')
        self.assertEqual('alice ➡️ bob 200🎪\n', emu.getRepliedText())

        await emu.sendMessage('alice', '/add 100\n@я 30\n@bob @eve\nkefir')
        self.assertEqual('Запомнил🍶 ждем  @bob @eve', emu.getRepliedText())

        await emu.sendMessage('bob', '/report')
        self.assertEqual('❗️ Есть незакрытая трата у @bob @eve\n\nalice ➡️ bob 200🎪\n', emu.getRepliedText())

        await emu.sendMessage('eve', '50', reply_id=6)
        self.assertEqual(constants.ReactionEmoji.THUMBS_UP, emu.getReaction())

        # игнорируем вопрос бота
        self.assertEqual('@bob должен 20?', emu.getRepliedText())

        await emu.sendMessage('alice', '/report')
        self.assertEqual('❗️ Есть незакрытая трата у @bob\n\nalice ➡️ bob 200🎪\n', emu.getRepliedText())

        await emu.sendMessage('bob', '20', reply_id=6)
        self.assertEqual(constants.ReactionEmoji.FIRE, emu.getReaction())

        await emu.sendMessage('eve', '/report')
        self.assertEqual('alice ➡️ bob 130🎪\neve ➡️ bob 50🎪\n', emu.getRepliedText())

    async def test_random_uncompleted_report(self):
        emu = ChatEmu()

        await emu.sendMessage('bob', '/add 200\n@alice @eve\ntea')
        self.assertEqual('Запомнил🍶 ждем  @alice @eve', emu.getRepliedText())
        
        await emu.sendMessage('alice', '/add 100\n@eve @bob\nkefir')
        self.assertEqual('Запомнил🍶 ждем  @eve @bob', emu.getRepliedText())
        
        await emu.sendMessage('eve', '/add 50\n@bob x\ncofe')
        self.assertEqual('Запомнил🍶', emu.getRepliedText())

        await emu.sendMessage('bob', '/report')
        replied_text = emu.getRepliedText()
        self.assertTrue(any(
            expected == replied_text
            for expected in [
                '❗️ Есть незакрытая трата у @alice @eve\n\nbob ➡️ eve 50🎪\n',
                '❗️ Есть незакрытая трата у @eve @bob\n\nbob ➡️ eve 50🎪\n'
            ]
        ))

        await emu.sendMessage('alice', '50', reply_id=2)
        self.assertEqual(constants.ReactionEmoji.THUMBS_UP, emu.getReaction())

        # игнорируем вопрос бота
        self.assertEqual('@eve должен 150?', emu.getRepliedText())

        await emu.sendMessage('eve', '150', reply_id=2)
        self.assertEqual(constants.ReactionEmoji.FIRE, emu.getReaction())

        await emu.sendMessage('alice', '/report')
        self.assertEqual('❗️ Есть незакрытая трата у @eve @bob\n\neve ➡️ bob 100🎪\nalice ➡️ bob 50🎪\n', emu.getRepliedText())

        await emu.sendMessage('bob', '80', reply_id=4)
        self.assertEqual(constants.ReactionEmoji.THUMBS_UP, emu.getReaction())

        # игнорируем вопрос бота
        self.assertEqual('@eve должен 20?', emu.getRepliedText())

        await emu.sendMessage('eve', '20', reply_id=4)
        self.assertEqual(constants.ReactionEmoji.FIRE, emu.getReaction())

        await emu.sendMessage('eve', '/report')
        self.assertEqual('eve ➡️ bob 70🎪\neve ➡️ alice 50🎪\n', emu.getRepliedText())

    async def test_last_debtor_approve(self):
        emu = ChatEmu()

        await emu.sendMessage('alice', '/add 500\n@bob\n@eve\ntea')
        self.assertEqual('Запомнил🍶 ждем  @bob @eve', emu.getRepliedText())

        await emu.sendMessage('eve', '200', reply_id=2) # Reply to 2 message in chat
        self.assertEqual(constants.ReactionEmoji.THUMBS_UP, emu.getReaction())
        self.assertEqual('@bob должен 300?', emu.getRepliedText())

        await emu.pressButton('bob', 'last-debtor-approve/yes', msg_id=4) # Press button on 4 message in chat
        self.assertEqual(constants.ReactionEmoji.FIRE, emu.getReaction())
        self.assertEqual('@bob согласился взять остаток 300', emu.getEditedText())

        await emu.sendMessage('alice', '/report')
        self.assertEqual('bob ➡️ alice 300🎪\neve ➡️ alice 200🎪\n', emu.getRepliedText())

        await emu.sendMessage('alice', '/add 100\n@bob 30\n@eve\n@alex\nburger')
        self.assertEqual('Запомнил🍶 ждем  @eve @alex', emu.getRepliedText())

        await emu.sendMessage('eve', '90', reply_id=8) # Reply to 2 message in chat
        self.assertEqual(constants.ReactionEmoji.THUMBS_UP, emu.getReaction())
        self.assertEqual('@alex должен -20?', emu.getRepliedText())

        await emu.pressButton('alex', 'last-debtor-approve/yes', msg_id=10) # Press button on 4 message in chat
        self.assertEqual(constants.ReactionEmoji.FIRE, emu.getReaction())
        self.assertEqual('@alex согласился взять остаток -20', emu.getEditedText())        

    async def test_last_debtor_papik_approve(self):
        emu = ChatEmu()

        await emu.sendMessage('alice', '/add 500\n@bob\n@eve\ntea')
        self.assertEqual('Запомнил🍶 ждем  @bob @eve', emu.getRepliedText())

        await emu.sendMessage('eve', '200', reply_id=2) # Reply to 2 message in chat
        self.assertEqual(constants.ReactionEmoji.THUMBS_UP, emu.getReaction())
        self.assertEqual('@bob должен 300?', emu.getRepliedText())

        await emu.pressButton('alice', 'last-debtor-approve/yes', msg_id=4) # Press button on 4 message in chat
        self.assertEqual(constants.ReactionEmoji.FIRE, emu.getReaction())
        self.assertEqual('@alice определил остаток @bob в 300', emu.getEditedText())

        await emu.sendMessage('alice', '/report')
        self.assertEqual('bob ➡️ alice 300🎪\neve ➡️ alice 200🎪\n', emu.getRepliedText())

        await emu.sendMessage('alice', '/add 100\n@bob 30\n@eve\n@alex\nburger')
        self.assertEqual('Запомнил🍶 ждем  @eve @alex', emu.getRepliedText())

        await emu.sendMessage('eve', '90', reply_id=8) # Reply to 2 message in chat
        self.assertEqual(constants.ReactionEmoji.THUMBS_UP, emu.getReaction())
        self.assertEqual('@alex должен -20?', emu.getRepliedText())

        await emu.pressButton('alice', 'last-debtor-approve/yes', msg_id=10) # Press button on 4 message in chat
        self.assertEqual(constants.ReactionEmoji.FIRE, emu.getReaction())
        self.assertEqual('@alice определил остаток @alex в -20', emu.getEditedText())        

    async def test_approve_negative_debt(self):
        emu = ChatEmu()

        await emu.sendMessage('alice', '/add 100\n@bob @eve @alex')
        self.assertEqual('Запомнил🍶 ждем  @bob @eve @alex', emu.getRepliedText())

        await emu.sendMessage('bob', '60', reply_id=2)
        self.assertEqual(constants.ReactionEmoji.THUMBS_UP, emu.getReaction())

        await emu.sendMessage('eve', '50', reply_id=2)
        self.assertEqual(constants.ReactionEmoji.THUMBS_UP, emu.getReaction())
        
        self.assertEqual('@alex должен -10?', emu.getRepliedText())
        await emu.pressButton('alex', 'last-debtor-approve/yes', msg_id=5)

        self.assertEqual(constants.ReactionEmoji.FIRE, emu.getReaction())
        self.assertEqual('@alex согласился взять остаток -10', emu.getEditedText())

        await emu.sendMessage('alice', '/report')
        self.assertEqual('bob ➡️ alice 60🎪\neve ➡️ alice 40🎪\neve ➡️ alex 10🎪\n', emu.getRepliedText())

    async def test_approve_zero_debt(self):
        emu = ChatEmu()

        await emu.sendMessage('alice', '/add 100\n@bob @eve @alex')
        self.assertEqual('Запомнил🍶 ждем  @bob @eve @alex', emu.getRepliedText())

        await emu.sendMessage('bob', '60', reply_id=2)
        self.assertEqual(constants.ReactionEmoji.THUMBS_UP, emu.getReaction())

        await emu.sendMessage('eve', '40', reply_id=2)
        self.assertEqual(constants.ReactionEmoji.THUMBS_UP, emu.getReaction())

        self.assertEqual('@alex должен 0?', emu.getRepliedText())
        await emu.pressButton('alex', 'last-debtor-approve/yes', msg_id=5)

        self.assertEqual(constants.ReactionEmoji.FIRE, emu.getReaction())
        self.assertEqual('@alex согласился взять остаток 0', emu.getEditedText())

        await emu.sendMessage('alice', '/report')
        self.assertEqual('bob ➡️ alice 60🎪\neve ➡️ alice 40🎪\n', emu.getRepliedText())


if __name__ == "__main__":
    unittest.main()
