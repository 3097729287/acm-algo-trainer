"""No network/accounts: event delivery, repeated runs and lock ordering."""
import json
import queue
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from external_browser import DevToolsPage, ExternalBrowserBridge
from assets import AssetLibrary
from backend import LocalServer
from training import ServiceError
import test_training as fixtures


class Socket:
    def __init__(self):
        self.incoming, self.sent = queue.Queue(), queue.Queue()

    def recv(self):
        value = self.incoming.get(timeout=2)
        if value is None:
            raise OSError('closed')
        return json.dumps(value)

    def send(self, raw):
        self.sent.put(json.loads(raw))

    def close(self):
        self.incoming.put(None)


class ReceiptDeliveryTests(unittest.TestCase):
    def test_unsolicited_receipt_and_callback_command_need_no_poll(self):
        socket, delivered, values = Socket(), threading.Event(), []
        def receive(event, page):
            values.append(event)
            values.append(page.call('Runtime.evaluate'))
            delivered.set()
        with patch('websocket.create_connection', return_value=socket):
            page = DevToolsPage('ws://127.0.0.1:1234/devtools/page/test', receive)
        try:
            socket.incoming.put({'method': 'Runtime.bindingCalled', 'params': {'name': '__tbReceipt', 'payload': 'AC'}})
            command = socket.sent.get(timeout=.5)
            socket.incoming.put({'id': command['id'], 'result': {'ack': True}})
            self.assertTrue(delivered.wait(.5), 'event delivery must not wait for the inspection timer')
            self.assertEqual(values, [{'name': '__tbReceipt', 'payload': 'AC'}, {'ack': True}])
        finally:
            page.close()

    def test_concurrent_out_of_order_responses_and_disconnect(self):
        socket, results = Socket(), {}
        with patch('websocket.create_connection', return_value=socket):
            page = DevToolsPage('ws://127.0.0.1:1234/devtools/browser/test', lambda *_: None)
        def call(name):
            try:
                results[name] = page.call(name, timeout=5)
            except OSError:
                results[name] = 'closed'
        threads = [threading.Thread(target=call, args=(name,)) for name in ('first', 'second')]
        try:
            for thread in threads:
                thread.start()
            commands = [socket.sent.get(timeout=.5) for _ in threads]
            for command in reversed(commands):
                socket.incoming.put({'id': command['id'], 'result': {'method': command['method']}})
            for thread in threads:
                thread.join(.5)
            self.assertEqual(results, {'first': {'method': 'first'}, 'second': {'method': 'second'}})
            waiter = threading.Thread(target=call, args=('disconnect',))
            waiter.start()
            socket.sent.get(timeout=.5)
            page.close()
            waiter.join(.5)
            self.assertFalse(waiter.is_alive())
            self.assertEqual(results['disconnect'], 'closed')
        finally:
            page.close()

    def test_final_status_is_pushed_only_after_durable_receipt(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            started, finish, pushed = threading.Event(), threading.Event(), []
            def save(*_):
                started.set()
                finish.wait(2)
                return {'id': 'persisted', 'verdict': 'AC', 'scope': 'official'}
            bridge = ExternalBrowserBridge(Path(directory), on_receipt=save, on_status=pushed.append)
            bridge.sessions['test'] = {'sessionId': 'test', 'status': 'judging', 'attempted': True}
            worker = threading.Thread(target=bridge._update, args=('test', {'status': 'finished', 'submissionId': '123', 'verdict': 'AC'}))
            worker.start()
            try:
                self.assertTrue(started.wait(.5))
                self.assertEqual(bridge.status('test')['status'], 'judging')
                self.assertEqual(pushed, [])
            finally:
                finish.set()
                worker.join(1)
                bridge.on_closing()
            self.assertEqual(pushed[0]['submission']['id'], 'persisted')
            self.assertTrue(pushed[0]['receiptSaved'])


class LocalRunTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown

    def test_custom_training_lists_read_committed_snapshot_during_busy_work(self):
        from custom_training_lists import read_lists, save_list
        save_list(self.service, {'title':'考前练习'})
        result, complete = [], threading.Event()
        def read():
            result.append(read_lists(self.service))
            complete.set()
        with self.service.lock:
            worker = threading.Thread(target=read)
            worker.start()
            self.assertTrue(complete.wait(.5), 'list loading waited for the judge/statistics lock')
        worker.join(1)
        self.assertEqual(result[0], read_lists(self.service))

    def test_twenty_runs_finish_with_push_without_network_or_workspace(self):
        original = self.assets.problem
        def cached(identity, fetch=True):
            self.assertFalse(fetch, 'local run must not wait for original-site network')
            return original(identity)
        self.assets.problem = cached
        finished, values = threading.Event(), []
        def receive(value):
            values.append(value['submission'])
            if value['submission']['finishedAt']:
                finished.set()
        self.service.on_submission = receive
        with patch.object(self.service, 'workspace', side_effect=AssertionError('local samples do not rebuild workspace')):
            for index in range(20):
                finished.clear()
                answer = self.service.submit(f'fixture::{chr(65 + index % 8)}', 'AC', mode='run', sample_run=True)
                self.assertTrue(finished.wait(1), f'run {index} failed to finish')
                result = self.service.submission(answer['submission']['id'])
                self.assertEqual(result['submission']['verdict'], 'SAMPLE_PASS')
                self.assertNotIn('workspace', result)
        self.assertEqual(len([value for value in values if value['finishedAt']]), 20)

    def test_update_waits_for_local_judge_and_then_proceeds(self):
        self.service.submit('fixture::A', 'BLOCK', mode='run')
        self.assertTrue(self.judge.started.wait(1))
        server = SimpleNamespace(training=self.service)
        with self.assertRaises(ServiceError) as issue:
            LocalServer.assert_update_ready(server)
        self.assertEqual(issue.exception.status, 409)
        self.judge.release.set()
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            with self.service.lock:
                if not self.service.connection.execute('SELECT 1 FROM submissions WHERE finished_at IS NULL').fetchone():
                    break
            time.sleep(.01)
        LocalServer.assert_update_ready(server)

    def test_asset_read_does_not_hold_lock_while_waiting_for_account_facts(self):
        waiting = threading.Event()
        def portable(identity):
            waiting.set()
            with self.service.lock:
                return {'statement': self.assets.problem(identity)}
        assets = AssetLibrary(SimpleNamespace(library=SimpleNamespace(statement=lambda _: None)), portable=portable)
        failures = []
        def read():
            try:
                with patch.object(assets, 'bundle', return_value={'scope':'samples', 'cases':[]}):
                    assets.problem('fixture::A', fetch=False)
            except Exception as error:
                failures.append(error)
        with self.service.lock:
            worker = threading.Thread(target=read)
            worker.start()
            self.assertTrue(waiting.wait(1))
            acquired = assets.lock.acquire(timeout=.3)
            if acquired:
                assets.lock.release()
        worker.join(1)
        self.assertTrue(acquired, 'asset/account locks have opposite acquisition order')
        self.assertFalse(worker.is_alive())
        self.assertEqual(failures, [])
        assets.close()
