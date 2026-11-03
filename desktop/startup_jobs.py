"""Start nonessential desktop jobs once, after real workspace content is served."""
import logging
import threading


class StartupJobs:
    def __init__(self, server, delay=2):
        self.server, self.delay = server, delay
        self.lock = threading.Lock()
        self.timer = None
        self.closed = False
        server.official_sync.defer_start = True

    def ready(self):
        with self.lock:
            if self.closed or self.timer is not None:
                return
            self.timer = threading.Timer(self.delay, self._start)
            self.timer.daemon = True
            self.timer.start()

    def _start(self):
        with self.lock:
            if self.closed:
                return
            self.server.official_sync.defer_start = False
            extensions = self.server.store.extensions
            extensions.auto_start = True
            actions = [self.server.official_sync.start]
            if extensions.state['settings']['autoSync']:
                actions.append(extensions.sync)
            actions.extend([self.server.content_updates.start, self.server.calendar_service])
            warm_browser=getattr(self.server,'warm_submission_browser',None)
            if callable(warm_browser):actions.append(warm_browser)
            actions.append(self.server.statement_backfill.start)
            for action in actions:
                try:
                    action()
                except Exception as issue:
                    logging.getLogger('tb.desktop').warning('Background startup deferred: %s', type(issue).__name__)

    def close(self):
        with self.lock:
            self.closed = True
            if self.timer is not None:
                self.timer.cancel()
