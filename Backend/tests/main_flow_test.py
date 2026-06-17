import utils
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


    async def test_add_spending_with_whitespaces(self):
        emu = ChatEmu()

        await emu.sendMessage('alice', '/add 2 +\t\xA0 2\n@bob 1+  1     + 1   +1\ntea')
        self.assertEqual('Запомнил🍶', emu.getRepliedText())
        
        await emu.sendMessage('alice', '/report')
        self.assertEqual('bob ➡️ alice 4🎪\n', emu.getRepliedText())

    async def test_add_spending_with_alternative_math_operators(self):
        emu = ChatEmu()

        await emu.sendMessage('alice', '/add 2×100 + 100⋅2\n@bob 1200÷3 + 0:2\ntea')
        self.assertEqual('Запомнил🍶', emu.getRepliedText())

        await emu.sendMessage('alice', '/report')
        self.assertEqual('bob ➡️ alice 400🎪\n', emu.getRepliedText())

    async def test_add_spending_sums_repeated_debtor_shares(self):
        emu = ChatEmu()

        await emu.sendMessage('alice', '/add 1000\n@alex 100\n@я x\n@alex 200')
        self.assertEqual('Запомнил🍶', emu.getRepliedText())

        await emu.sendMessage('alice', '/report')
        self.assertEqual('alex ➡️ alice 300🎪\n', emu.getRepliedText())

    async def test_add_spending_sums_repeated_debtor_group_share(self):
        emu = ChatEmu()

        await emu.sendMessage('alice', '/add 1000\n@alex @я 200*1.5\n@alex 400')
        self.assertEqual('Запомнил🍶', emu.getRepliedText())

        await emu.sendMessage('alice', '/report')
        self.assertEqual('alex ➡️ alice 700🎪\n', emu.getRepliedText())


    async def test_reply_spending(self):
        emu = ChatEmu()

        await emu.sendMessage('alice', '/add 200\n@bob 50\n@eve\ntea')
        self.assertEqual('Запомнил🍶 ждем  @eve', emu.getRepliedText())

        await emu.sendMessage('eve', '150', reply_id=2) # Reply to 2 message in chat
        self.assertEqual(constants.ReactionEmoji.FIRE, emu.getReaction())

        await emu.sendMessage('alice', '/report')
        self.assertEqual('eve ➡️ alice 150🎪\nbob ➡️ alice 50🎪\n', emu.getRepliedText())

    async def test_reply_saves_unbalanced_spending(self):
        for last_share, error in (('300', 'не хватает 100'), ('500', 'лишние 100')):
            with self.subTest(last_share=last_share):
                emu = ChatEmu()

                await emu.sendMessage('Artyom', '/add 1000\n@Filipp @Grisha @Amir')
                emu.getRepliedText()

                await emu.sendMessage('Filipp', '300', reply_id=2)
                self.assertEqual(constants.ReactionEmoji.THUMBS_UP, emu.getReaction())
                await emu.sendMessage('Grisha', '300', reply_id=2)
                self.assertEqual(constants.ReactionEmoji.THUMBS_UP, emu.getReaction())
                emu.getRepliedText()
                await emu.sendMessage('Amir', last_share, reply_id=2)
                self.assertEqual(constants.ReactionEmoji.THINKING_FACE, emu.getReaction())
                self.assertEqual(f'Принято, но не сошлось: {error}', emu.getRepliedText())

                await emu.sendMessage('Artyom', '/report')
                self.assertEqual(
                    f'@Filipp @Grisha @Amir @Artyom, в вашей трате не сошлось: {error}\n\n⚠️ Нет записанных трат',
                    emu.getRepliedText()
                )

    async def test_add_rejects_unbalanced_spending(self):
        for shares, error in (
            (('@Filipp 300', '@Grisha 300', '@Amir 300'), 'Не сошлось: не хватает 100'),
            (('@Filipp 400', '@Grisha 400', '@Amir 400'), 'Не сошлось: лишние 200'),
        ):
            with self.subTest(shares=shares):
                emu = ChatEmu()
                with self.assertRaisesRegex(utils.BotException, error):
                    await emu.sendMessage('Artyom', '/add 1000\n' + '\n'.join(shares))

                await emu.sendMessage('Artyom', '/report')
                self.assertEqual('⚠️ Нет записанных трат', emu.getRepliedText())

    async def test_usernames_are_case_insensitive(self):
        emu = ChatEmu()

        await emu.sendMessage('Alice', '/add 100\n@Bob @bob\ntea')
        self.assertEqual('Запомнил🍶 ждем  @bob', emu.getRepliedText())

        await emu.sendMessage('BOB', '100', reply_id=2)
        self.assertEqual(constants.ReactionEmoji.FIRE, emu.getReaction())

        await emu.sendMessage('ALICE', '/report')
        self.assertEqual('bob ➡️ Alice 100🎪\n', emu.getRepliedText())

    async def test_report_uses_last_mentioned_username_case(self):
        emu = ChatEmu()

        await emu.sendMessage('alice', '/add 100\n@ALEX 100\ntea')
        self.assertEqual('Запомнил🍶', emu.getRepliedText())

        await emu.sendMessage('alice', '/add 50\n@Alex 50\ncoffee')
        self.assertEqual('Запомнил🍶', emu.getRepliedText())

        await emu.sendMessage('alice', '/report')
        self.assertEqual('Alex ➡️ alice 150🎪\n', emu.getRepliedText())

    async def test_report_prioritizes_sender_username_case(self):
        scenarios = (
            (60, '@Bob 30\n@Anna 30'),
            (90, '@Bob 30\n@Alex 30\n@Anna 30'),
        )
        for amount, debtors in scenarios:
            with self.subTest(debtors=debtors):
                emu = ChatEmu()

                await emu.sendMessage('Bob', '/add 90\n@Alex 30\n@Bob 30\n@Anna 30')
                self.assertEqual('Запомнил🍶', emu.getRepliedText())

                await emu.sendMessage('ALEX', f'/add {amount}\n{debtors}')
                self.assertEqual('Запомнил🍶', emu.getRepliedText())

                await emu.sendMessage('Anna', '/report')
                self.assertEqual('Anna ➡️ ALEX 30🎪\nAnna ➡️ Bob 30🎪\n', emu.getRepliedText())

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

    async def test_reply_add_debt_with_ellipsis(self):
        emu = ChatEmu()

        await emu.sendMessage('bob', '/add 500\n@alice 30\n@eve @bob')
        self.assertEqual('Запомнил🍶 ждем  @eve @bob', emu.getRepliedText())

        await emu.sendMessage('eve', '200', reply_id=2)
        self.assertEqual(constants.ReactionEmoji.THUMBS_UP, emu.getReaction())
        self.assertEqual('@bob должен 270?', emu.getRepliedText()) # игнорим

        await emu.sendMessage('alice', '…+150', reply_id=2)
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
        
        await emu.sendMessage('bob', '/report')
        replied_text = emu.getRepliedText()
        self.assertTrue(any(
            expected == replied_text
            for expected in [
                '❗️ Есть незакрытая трата у @alice @eve\n\n⚠️ Нет записанных трат',
                '❗️ Есть незакрытая трата у @eve @bob\n\n⚠️ Нет записанных трат'
            ]
        ))

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
        self.assertEqual('@alice определил долю @bob в 300', emu.getEditedText())

        await emu.sendMessage('alice', '/report')
        self.assertEqual('bob ➡️ alice 300🎪\neve ➡️ alice 200🎪\n', emu.getRepliedText())

        await emu.sendMessage('alice', '/add 100\n@bob 30\n@eve\n@alex\nburger')
        self.assertEqual('Запомнил🍶 ждем  @eve @alex', emu.getRepliedText())

        await emu.sendMessage('eve', '90', reply_id=8) # Reply to 2 message in chat
        self.assertEqual(constants.ReactionEmoji.THUMBS_UP, emu.getReaction())
        self.assertEqual('@alex должен -20?', emu.getRepliedText())

        await emu.pressButton('alice', 'last-debtor-approve/yes', msg_id=10) # Press button on 4 message in chat
        self.assertEqual(constants.ReactionEmoji.FIRE, emu.getReaction())
        self.assertEqual('@alice определил долю @alex в -20', emu.getEditedText())        

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

    async def test_reset(self):
        emu = ChatEmu()

        await emu.sendMessage('alice', '/add 100\n@bob @eve @alex')
        self.assertEqual('Запомнил🍶 ждем  @bob @eve @alex', emu.getRepliedText())

        await emu.sendMessage('bob', '/add 200\n@bob @eve @alex x')
        self.assertEqual('Запомнил🍶', emu.getRepliedText())

        await emu.sendMessage('alice', '/report')
        self.assertEqual('❗️ Есть незакрытая трата у @bob @eve @alex\n\nalex ➡️ bob 66.67🎪\neve ➡️ bob 66.67🎪\n', emu.getRepliedText())

        await emu.sendMessage('alice', '/reset')
        self.assertEqual('@alice @bob', emu.getRepliedText())

        await emu.pressButton('alex', 'reset-costs', msg_id=8)
        try:
            self.assertEqual('Z Z Z', emu.getEditedText())
        except IndexError:
            pass
        except Exception as e:
            self.fail(f"Unexpected exception raised: {e}")
        else:
            self.fail("Expected IndexError, but no exception was raised")
        
        await emu.pressButton('alice', 'reset-costs', msg_id=8)
        self.assertEqual('@bob', emu.getEditedText())

        await emu.pressButton('alice', 'reset-costs', msg_id=8)
        try:
            self.assertEqual('Z Z Z', emu.getEditedText())
        except IndexError:
            pass
        except Exception as e:
            self.fail(f"Unexpected exception raised: {e}")
        else:
            self.fail("Expected IndexError, but no exception was raised")

        await emu.pressButton('bob', 'reset-costs', msg_id=8)
        self.assertEqual('Траты сброшены💨', emu.getEditedText())

        await emu.sendMessage('eve', '/report')
        self.assertEqual('⚠️ Нет записанных трат', emu.getRepliedText())
    
    async def test_spending_with_s(self):
        emu = ChatEmu()

        await emu.sendMessage('alice', '/add 300\n@bob s/3\n@eve\ntea')
        self.assertEqual('Запомнил🍶 ждем  @eve', emu.getRepliedText())

        await emu.sendMessage('eve', 's/2 + 50', reply_id=2) # Reply to 2 message in chat
        self.assertEqual(constants.ReactionEmoji.FIRE, emu.getReaction())

        await emu.sendMessage('alice', '/report')
        self.assertEqual('eve ➡️ alice 200🎪\nbob ➡️ alice 100🎪\n', emu.getRepliedText())
    
    async def test_add_for_everyone(self):
        emu = ChatEmu()

        # First, create some spendings to establish users in the group
        await emu.sendMessage('alice', '/add 100\n@bob 50\n@charlie 50')
        self.assertEqual('Запомнил🍶', emu.getRepliedText())
        
        # Now add an expense with no debtors specified - should split among all users
        await emu.sendMessage('alice', '/add 600\ntaxi')
        self.assertEqual('Запомнил🍶', emu.getRepliedText())
        
        # Check report: 600 split equally among alice, bob, charlie (3 users) = 200 each
        # Since alice paid, bob and charlie owe alice 200 each
        await emu.sendMessage('alice', '/report')
        self.assertEqual('bob ➡️ alice 250🎪\ncharlie ➡️ alice 250🎪\n', emu.getRepliedText())

    async def test_spending_report(self):
        emu = ChatEmu()

        await emu.sendMessage('a', '/add 1000\n@a 400+x+x\n@b 200+x+x+x\n@c\n@d 50+30\ntea')
        self.assertEqual('Запомнил🍶 ждем  @c', emu.getRepliedText())

        await emu.sendMessage('a', '/report', reply_id=2) # Reply to 2 message in chat
        self.assertEqual('Сумма: 1000\n\n@a 400+x+x (400 + 2x)\n@b 200+x+x+x (200 + 3x)\n@c не заполнил\n@d 80', emu.getRepliedText())
    
    async def test_spending_adding_errors(self):
        emu = ChatEmu()

        with self.assertRaisesRegex(utils.BotWrongInputException, 'На первой строке нужно указать сумму'):
            await emu.sendMessage('alice', '/add\n@a 4')

        with self.assertRaisesRegex(utils.BotWrongInputException, 'Некорректная сумма у должника'):
            await emu.sendMessage('alice', '/add 300\n@a test')
        
        with self.assertRaisesRegex(utils.BotWrongInputException, 'Не указаны должники'):
            await emu.sendMessage('alice', '/add 300')
    
    async def test_spending_adding_wrong_input_errors(self):
        emu = ChatEmu()

        with self.assertRaisesRegex(utils.BotWrongInputException, "Значение должно быть числом или переменной. Сейчас - '300x'"):
            await emu.sendMessage('alice', '/add 500\n@bob 200*x\n@alice 300 x')

if __name__ == "__main__":
    unittest.main()
