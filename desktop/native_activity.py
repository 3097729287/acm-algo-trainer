"""Read-only activity metadata for the desktop and its native WebView2 children.

Snapshots contain no key values, coordinates, page messages or chat text.
Windows provenance and HWND ownership are checked before counting input;
registered command keys retain only their transient held state for repeat.
"""
from __future__ import annotations
import ctypes
import os
import secrets
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
        self.thread_id = 0
        self.ready = threading.Event()
        self.hwnd = 0
        self.main_webview = 0
        self.shortcuts = shortcuts

    def snapshot(self):
        # Deliberately no account restore, sync, navigation or activity writes.
        with self.lock:
            return {'available': self.available and not self.closed,
                    'session': self.session, 'revision': self.revision,
                    'observed': self.last_input is not None,
                    'ageSeconds': max(0., self.clock() - self.last_input) if self.last_input is not None else None}

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
                return
            self.started = True
            self.thread = threading.Thread(target=self._run, name='tb-native-input', daemon=True)
            self.thread.start()

    def _run(self):
        from ctypes import wintypes as W
        user = ctypes.WinDLL('user32', use_last_error=True)
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        result = ctypes.c_ssize_t
        hook_proc = ctypes.WINFUNCTYPE(result, ctypes.c_int, ctypes.c_size_t, ctypes.c_ssize_t)

        class Mouse(ctypes.Structure):
            _fields_ = [('point', W.POINT), ('data', W.DWORD), ('flags', W.DWORD),
                        ('time', W.DWORD), ('extra', ctypes.c_size_t)]

        class Keyboard(ctypes.Structure):
            # Key is inspected only for registered app combinations. No text,
            # scan code, key history, timestamp or extra input data is retained.
            _fields_ = [('key', W.DWORD), ('scan', W.DWORD), ('flags', W.DWORD),
                        ('time', W.DWORD), ('extra', ctypes.c_size_t)]

        class GUIThread(ctypes.Structure):
            _fields_ = [('size', W.DWORD), ('flags', W.DWORD), ('active', W.HWND), ('focus', W.HWND),
                        ('capture', W.HWND), ('menu', W.HWND), ('move', W.HWND), ('caret', W.HWND), ('rect', W.RECT)]

        user.SetWindowsHookExW.argtypes = [ctypes.c_int, hook_proc, W.HINSTANCE, W.DWORD]
        user.SetWindowsHookExW.restype = W.HANDLE
        user.CallNextHookEx.argtypes = [W.HANDLE, ctypes.c_int, ctypes.c_size_t, ctypes.c_ssize_t]
        user.CallNextHookEx.restype = result
        user.UnhookWindowsHookEx.argtypes = [W.HANDLE]
        user.UnhookWindowsHookEx.restype = W.BOOL
        user.GetAncestor.argtypes, user.GetAncestor.restype = [W.HWND, W.UINT], W.HWND
        user.GetForegroundWindow.restype = W.HWND
        user.WindowFromPoint.argtypes, user.WindowFromPoint.restype = [W.POINT], W.HWND
        user.IsWindow.argtypes, user.IsWindow.restype = [W.HWND], W.BOOL
        user.IsChild.argtypes, user.IsChild.restype = [W.HWND, W.HWND], W.BOOL
        user.GetGUIThreadInfo.argtypes, user.GetGUIThreadInfo.restype = [W.DWORD, ctypes.POINTER(GUIThread)], W.BOOL
        user.GetAsyncKeyState.argtypes, user.GetAsyncKeyState.restype = [ctypes.c_int], ctypes.c_short
        user.GetMessageW.argtypes = [ctypes.POINTER(W.MSG), W.HWND, W.UINT, W.UINT]
        user.GetMessageW.restype = W.BOOL
        user.PeekMessageW.argtypes = [ctypes.POINTER(W.MSG), W.HWND, W.UINT, W.UINT, W.UINT]
        user.PeekMessageW.restype = W.BOOL
        user.TranslateMessage.argtypes = [ctypes.POINTER(W.MSG)]
        user.DispatchMessageW.argtypes, user.DispatchMessageW.restype = [ctypes.POINTER(W.MSG)], result
        kernel.GetModuleHandleW.argtypes, kernel.GetModuleHandleW.restype = [W.LPCWSTR], W.HMODULE
        kernel.GetCurrentThreadId.restype = W.DWORD

        def owned(handle):
            # GA_ROOTOWNER includes the app's owned login windows, but excludes
            # every other app and its WebView2/browser windows.
            return bool(handle and user.IsWindow(self.hwnd)
                        and user.GetAncestor(handle, 3) == self.hwnd)

        @hook_proc
        def mouse(code, message, pointer):
            if code == 0:
                try:
                    event = ctypes.cast(pointer, ctypes.POINTER(Mouse)).contents
                    # Coordinates exist only for this OS hit-test. They are
                    # never copied into the activity object or any response.
                    self._observe('mouse', event.flags,
                                  not event.flags & 0x03 and owned(user.WindowFromPoint(event.point)))
                except Exception:
                    pass
            return user.CallNextHookEx(None, code, message, pointer)

        @hook_proc
        def keyboard(code, message, pointer):
            if code == 0:
                try:
                    event = ctypes.cast(pointer, ctypes.POINTER(Keyboard)).contents
                    foreground_owned = owned(user.GetForegroundWindow())
                    self._observe('keyboard', event.flags, foreground_owned)
                    if self.shortcuts is not None and self.shortcuts.listening() and not event.flags & 0x12:
                        info = GUIThread();info.size = ctypes.sizeof(info)
                        focus = info.focus if foreground_owned and user.GetGUIThreadInfo(0, ctypes.byref(info)) else None
                        # Main DOM already routes registered combinations in
                        # capture phase. Forward only the native child/owned
                        # site window to prevent two executions of one input.
                        child = bool(foreground_owned and focus and self.main_webview
                                     and focus != self.main_webview and not user.IsChild(self.main_webview, focus))
                        pressed = lambda key: bool(user.GetAsyncKeyState(key) & 0x8000)
                        if (child or self.shortcuts.has_held()) and self.shortcuts.key(event.key, event.flags, child_owned=child,
                                control=pressed(0x11), alt=pressed(0x12), shift=pressed(0x10),
                                meta=pressed(0x5B) or pressed(0x5C)):
                            return 1
                except Exception:
                    pass
            return user.CallNextHookEx(None, code, message, pointer)

        hooks = []
        try:
            # Keep callback references on this thread's stack throughout the
            # message pump. The callback never blocks on UI, network or disk.
            self.thread_id = kernel.GetCurrentThreadId()
            message = W.MSG()
            user.PeekMessageW(ctypes.byref(message), None, 0, 0, 0)
            module = kernel.GetModuleHandleW(None)
            for kind, callback in ((14, mouse), (13, keyboard)):
                handle = user.SetWindowsHookExW(kind, callback, module, 0)
                if not handle:
                    raise ctypes.WinError(ctypes.get_last_error())
                hooks.append(handle)
            with self.lock:
                self.available = not self.closed
            self.ready.set()
            while not self.closed:
                answer = user.GetMessageW(ctypes.byref(message), None, 0, 0)
                if answer <= 0:
                    break
                user.TranslateMessage(ctypes.byref(message))
                user.DispatchMessageW(ctypes.byref(message))
        except Exception:
            # DOM input still works when Windows declines a native hook. Never
            # turn setup failure or polling into a synthetic activity signal.
            pass
        finally:
            for handle in hooks:
                user.UnhookWindowsHookEx(handle)
            with self.lock:
                self.available = False
            self.ready.set()

    def close(self):
        with self.lock:
            self.closed, self.available = True, False
            thread_id, thread = self.thread_id, self.thread
        if thread_id and os.name == 'nt':
            from ctypes import wintypes as W
            user = ctypes.WinDLL('user32', use_last_error=True)
            user.PostThreadMessageW.argtypes = [W.DWORD, W.UINT, ctypes.c_size_t, ctypes.c_ssize_t]
            user.PostThreadMessageW(thread_id, 0x0012, 0, 0)  # WM_QUIT
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=1)


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
