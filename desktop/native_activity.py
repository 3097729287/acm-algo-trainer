"""Read-only activity metadata for the desktop and its native WebView2 children.

Snapshots contain no key values, coordinates, page messages or chat text.
Windows provenance and HWND ownership are checked before counting input;
registered command keys retain only their transient held state for repeat.
"""
from __future__ import annotations
import os
import secrets
import logging
import threading
import time


def physical_input(kind, flags, owned):
    """Reject injected input, including lower-integrity injected input."""
    if not owned:
        return False
    if kind == 'keyboard':
        return not flags & 0x12  # LLKHF_INJECTED | LLKHF_LOWER_IL_INJECTED
    if kind == 'mouse':
        return not flags & 0x03  # LLMHF_INJECTED | LLMHF_LOWER_IL_INJECTED
    return False


class NativeActivity:
    def __init__(self, *, clock=time.monotonic, shortcuts=None):
        self.clock = clock
        self.lock = threading.Lock()
        self.session = secrets.token_hex(16)
        self.revision = 0
        self.last_input = None
        self.available = self.closed = self.started = False
        self.thread = None
        self.ready = threading.Event()
        self.hwnd = 0
        self.main_webview = 0
        self.shortcuts = shortcuts
        self.native = None
        self.error_code = None

    def snapshot(self):
        # No account restore, sync, navigation or activity writes. A managed
        # immutable snapshot keeps revision and event time from one observation.
        with self.lock:
            native, closed, session = self.native, self.closed, self.session
        if native is not None:
            value = native.Snapshot()
            return {'available': bool(value.Available and not closed), 'session': session,
                    'revision': int(value.Revision), 'observed': bool(value.Observed),
                    'ageSeconds': float(value.AgeSeconds) if value.Observed else None}
        with self.lock:
            return {'available': self.available and not self.closed,
                    'session': self.session, 'revision': self.revision,
                    'observed': self.last_input is not None,
                    'ageSeconds': max(0., self.clock() - self.last_input) if self.last_input is not None else None}

    def diagnostics(self):
        with self.lock:
            native, code = self.native, self.error_code
        return {'backend': 'managed-windows-input', 'errorCode': code or (str(native.ErrorCode) if native is not None and native.ErrorCode else None),
                'started': self.started, 'closed': self.closed}

    def _observe(self, kind, flags, owned):
        if not physical_input(kind, flags, owned):
            return
        with self.lock:
            if self.closed:
                return
            self.revision += 1
            self.last_input = self.clock()

    def start(self, hwnd, main_webview=0):
        if os.name != 'nt' or not hwnd:
            return
        with self.lock:
            if self.closed:
                return
            self.hwnd = int(hwnd)
            if main_webview:
                self.main_webview = int(main_webview)
            if self.started:
                if self.native is not None:
                    self.native.SetHandles(self.hwnd, self.main_webview)
                return
            self.started = True
            self.thread = threading.Thread(target=self._run, name='tb-native-input', daemon=True)
            self.thread.start()

    def _run(self):
        native = None
        try:
            from native_activity_host import managed_type
            native = managed_type()(self.hwnd, self.main_webview)
            with self.lock:
                if self.closed:
                    native.Dispose()
                    return
                self.native = native
            if self.shortcuts is not None:
                self.shortcuts.attach_native(native)
            native.Start()
            if not native.WaitReady(2000) or not native.Snapshot().Available:
                with self.lock:
                    if self.closed:
                        return
                raise RuntimeError('NATIVE_INPUT_START_FAILED')
            with self.lock:
                self.available = not self.closed
        except Exception:
            if native is not None:
                try:
                    native.Dispose()
                except Exception:
                    pass
            with self.lock:
                self.available, self.native, self.error_code = False, None, 'NATIVE_INPUT_INITIALIZATION_FAILED'
            if self.shortcuts is not None:
                self.shortcuts.native_failed(self.error_code)
            logging.getLogger('tb.native_input').warning('Native input unavailable: %s', self.error_code)
        finally:
            self.ready.set()

    def close(self):
        with self.lock:
            self.closed, self.available = True, False
            native, thread = self.native, self.thread
        if native is not None:
            native.Dispose()
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2)


def bind(server, window, shortcuts=None):
    activity = NativeActivity(shortcuts=shortcuts)
    server.native_activity = activity
    attached = [False]

    def start(*_):
        native = getattr(window, 'native', None)
        if native is not None and not native.IsDisposed and native.IsHandleCreated:
            main = native.browser.webview
            activity.start(native.Handle.ToInt64(), main.Handle.ToInt64() if main.IsHandleCreated else 0)
            if not attached[0]:
                attached[0] = True
                native.HandleCreated += start
                main.HandleCreated += start

    window.events.shown += start
    window.events.loaded += start
    start()  # Initialization can finish after the window's shown event.
    return activity
