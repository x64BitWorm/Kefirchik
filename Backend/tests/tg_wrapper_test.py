import asyncio
import time
import unittest
from unittest.mock import AsyncMock, Mock, patch

from telegram.error import NetworkError
from telegram.ext import ExtBot

from tg_wrapper import POLLING_WATCHDOG_TIMEOUT, PollingTracker, TgWrapper, TrackedExtBot


class TrackedExtBotTest(unittest.TestCase):
    def test_get_updates_clears_request_marker_after_success(self):
        tracker = PollingTracker()
        bot = TrackedExtBot(token='123:test', polling_tracker=tracker)

        with patch.object(ExtBot, 'get_updates', new=AsyncMock(return_value=())):
            asyncio.run(bot.get_updates())

        self.assertIsNone(tracker.request_started_at)

    def test_get_updates_clears_request_marker_after_network_error(self):
        tracker = PollingTracker()
        bot = TrackedExtBot(token='123:test', polling_tracker=tracker)

        with patch.object(
            ExtBot,
            'get_updates',
            new=AsyncMock(side_effect=NetworkError('network unavailable')),
        ):
            with self.assertRaises(NetworkError):
                asyncio.run(bot.get_updates())

        self.assertIsNone(tracker.request_started_at)


class PollingWatchdogTest(unittest.IsolatedAsyncioTestCase):
    async def test_stalled_polling_stops_application(self):
        wrapper = TgWrapper.__new__(TgWrapper)
        wrapper.pollingTracker = PollingTracker()
        wrapper.pollingTracker.request_started_at = time.monotonic() - POLLING_WATCHDOG_TIMEOUT - 1
        wrapper.pollingStalled = False
        application = Mock()

        with patch('tg_wrapper.asyncio.sleep', new=AsyncMock()):
            await wrapper._polling_watchdog(application)

        self.assertTrue(wrapper.pollingStalled)
        application.stop_running.assert_called_once_with()

    async def test_network_retry_delay_does_not_stop_application(self):
        wrapper = TgWrapper.__new__(TgWrapper)
        wrapper.pollingTracker = PollingTracker()
        wrapper.pollingStalled = False
        application = Mock()

        async def stop_after_first_check(_):
            raise asyncio.CancelledError

        with patch('tg_wrapper.asyncio.sleep', new=stop_after_first_check):
            with self.assertRaises(asyncio.CancelledError):
                await wrapper._polling_watchdog(application)

        self.assertFalse(wrapper.pollingStalled)
        application.stop_running.assert_not_called()
