"""Bounded connector startup and cleanup, without WebView or original sites."""
import queue
from types import SimpleNamespace
import unittest

from browser_bridge import BrowserBridge
from silent_submit import SilentSubmitter


class SilentLifecycleTests(unittest.TestCase):
    def make(self, cached=None):
        waits, wakes, finishes = [], [], []
        event = SimpleNamespace(wait=lambda seconds: waits.append(seconds) or False)
        store = SimpleNamespace(snapshot=lambda platform: cached,
                                request=lambda platform: event,
                                finish=finishes.append)
        bridge = BrowserBridge('http://127.0.0.1:1', session_store=store)
        runner = SilentSubmitter(object(), bridge, store, wake=lambda: wakes.append(True))
        runner._ui = lambda action: action()
        bridge.runner = runner
        # Create the job without spawning its real worker.
        original_start = runner.start
        runner.start = lambda identity: None
        sid = bridge.submit('https://codeforces.com/contest/123/problem/A', 'int main(){}', 'fixture')['sessionId']
        runner.start = original_start
        return bridge, runner, sid, waits, wakes, finishes

    def test_connected_extension_with_no_snapshot_finishes_without_worker_restart(self):
        bridge, runner, sid, waits, wakes, finishes = self.make()
        bridge._session_client = lambda platform, **kwargs: 'connected-profile'
        restarted = []
        runner.start = restarted.append
        runner._run(sid)
        self.assertEqual(bridge.status(sid)['status'], 'needs_browser')
        self.assertFalse(bridge.sessions[sid]['intent'])
        self.assertEqual(waits, [1, 12])
        self.assertEqual(wakes, [True])
        self.assertEqual(finishes, ['Codeforces'])
        self.assertEqual(restarted, [])
        self.assertNotIn(sid, runner.messages)
        self.assertNotIn(sid, runner.threads)

    def test_cached_login_does_not_wait_for_cold_browser_and_queue_is_released(self):
        cached = {'cookies': [{'value': 'fixture'}], 'loginState': 'logged_in'}
        bridge, runner, sid, waits, wakes, _ = self.make(cached)
        runner._attach_silent = lambda identity, snapshot: bridge.sessions[identity].update(status='closed')
        runner._run(sid)
        self.assertEqual(waits, [1.5])
        self.assertEqual(wakes, [])
        self.assertNotIn(sid, runner.messages)

    def test_late_native_callback_does_not_retain_finished_queue(self):
        _, runner, sid, *_ = self.make()
        runner.messages[sid] = queue.Queue()
        runner._message(sid, {'tick': True})
        self.assertEqual(runner.messages[sid].get_nowait(), {'tick': True})
        runner.messages.pop(sid)
        runner._message(sid, {'tick': True})
        self.assertEqual(runner.messages, {})


if __name__ == '__main__':
    unittest.main()
