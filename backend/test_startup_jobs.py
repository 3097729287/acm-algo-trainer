from threading import Event
from types import SimpleNamespace
import time
import unittest
from unittest.mock import Mock

from startup_jobs import StartupJobs


class StartupJobsTests(unittest.TestCase):
    def server(self):
        done=Event()
        return SimpleNamespace(official_sync=SimpleNamespace(start=Mock()),
            store=SimpleNamespace(extensions=SimpleNamespace(auto_start=False,state={'settings':{'autoSync':True}},sync=Mock())),
            content_updates=SimpleNamespace(start=Mock()),calendar_service=Mock(),
            statement_backfill=SimpleNamespace(start=Mock(side_effect=done.set))),done

    def test_jobs_wait_for_real_workspace_and_start_once_after_it(self):
        server,done=self.server();jobs=StartupJobs(server,delay=.02)
        try:
            time.sleep(.03);server.official_sync.start.assert_not_called()
            self.assertTrue(server.official_sync.defer_start)
            jobs.ready();jobs.ready();self.assertTrue(done.wait(2))
            jobs.ready();server.official_sync.start.assert_called_once()
            server.store.extensions.sync.assert_called_once();server.calendar_service.assert_called_once()
            self.assertFalse(server.official_sync.defer_start)
            self.assertTrue(server.store.extensions.auto_start)
        finally:jobs.close()

    def test_close_cancels_pending_jobs_and_respects_disabled_public_sync(self):
        server,done=self.server();jobs=StartupJobs(server,delay=.05);jobs.ready();jobs.close()
        self.assertFalse(done.wait(.1));server.official_sync.start.assert_not_called()
        server,done=self.server();server.store.extensions.state['settings']['autoSync']=False
        jobs=StartupJobs(server,delay=0)
        try:
            jobs.ready();self.assertTrue(done.wait(2));server.store.extensions.sync.assert_not_called()
        finally:jobs.close()
