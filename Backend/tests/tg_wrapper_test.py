import asyncio
import time
import unittest
from unittest.mock import AsyncMock, Mock, patch

from telegram.ext import ExtBot

from tg_wrapper import POLLING_WATCHDOG_TIMEOUT, PollingTracker, TgWrapper, TrackedExtBot


class TrackedExtBotTest(unittest.TestCase):
    def test_get_updates_refreshes_polling_timestamp(self):
        tracker = PollingTracker()
        tracker.last_success = 0
        bot = TrackedExtBot(token='123:test', polling_tracker=tracker)

        with patch.object(ExtBot, 'get_updates', new=AsyncMock(return_value=())):
            asyncio.run(bot.get_updates())

        self.assertGreater(tracker.last_success, 0)


class PollingWatchdogTest(unittest.IsolatedAsyncioTestCase):
    async def test_stalled_polling_stops_application(self):
        wrapper = TgWrapper.__new__(TgWrapper)
        wrapper.pollingTracker = PollingTracker()
        wrapper.pollingTracker.last_success = time.monotonic() - POLLING_WATCHDOG_TIMEOUT - 1
        wrapper.pollingStalled = False
        application = Mock()

        with patch('tg_wrapper.asyncio.sleep', new=AsyncMock()):
            await wrapper._polling_watchdog(application)

        self.assertTrue(wrapper.pollingStalled)
        application.stop_running.assert_called_once_with()
