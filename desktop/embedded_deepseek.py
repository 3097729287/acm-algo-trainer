"""An account-owned WebView2 child, with no host bridge or shared browser data."""
from __future__ import annotations
import hashlib
import hmac
import json
import math
from pathlib import Path
import re
import secrets
import threading
import time
from urllib.parse import urlsplit

from training import ServiceError
from native_shortcuts import NativeShortcuts, validate_registration

TARGET = 'https://chat.deepseek.com/'
_ID = re.compile(r'[a-f0-9-]{16,64}')
_CAP = re.compile(r'[a-f0-9]{64}')


def profile_key(owner):
    return hashlib.sha256(json.dumps(list(owner[:2]), ensure_ascii=True, separators=(',', ':')).encode()).hexdigest()


def frame(value):
    allowed = {'viewId', 'sequence', 'ownerKey', 'visible', 'rect', 'viewport', 'retry', 'shortcuts'}
    if not isinstance(value, dict) or set(value) - allowed:
        raise ServiceError(400, '网页位置请求无效')
    if (not isinstance(value.get('viewId'), str) or not _ID.fullmatch(value['viewId'])
            or type(value.get('sequence')) is not int or not 0 < value['sequence'] < 2**53
            or not isinstance(value.get('ownerKey'), str) or not _CAP.fullmatch(value['ownerKey'])
            or type(value.get('visible')) is not bool or type(value.get('retry', False)) is not bool):
        raise ServiceError(400, '网页位置请求无效')
    if not value['visible']:
        return dict(value)
    validate_registration(value.get('shortcuts'))
    rect, viewport = value.get('rect'), value.get('viewport')
    if (not isinstance(rect, dict) or set(rect) != {'x', 'y', 'width', 'height'}
            or not isinstance(viewport, dict) or set(viewport) != {'width', 'height'}):
        raise ServiceError(400, '网页位置请求无效')
    if not all(type(n) in (float, int) and math.isfinite(n) and 0 <= n <= 32768 for n in (*rect.values(), *viewport.values())):
        raise ServiceError(400, '网页位置请求无效')
    if (min(rect['width'], rect['height'], viewport['width'], viewport['height']) <= 0
            or rect['x'] + rect['width'] > viewport['width'] + .5
            or rect['y'] + rect['height'] > viewport['height'] + .5):
        raise ServiceError(400, '网页位置超出窗口')
    return dict(value)


def pixel_bounds(rect, viewport, host):
    """CSS viewport -> actual host client pixels, including DPI and web zoom."""
    sx, sy = host[2] / viewport['width'], host[3] / viewport['height']
    left = max(0, min(host[2], round(rect['x'] * sx)))
    top = max(0, min(host[3], round(rect['y'] * sy)))
    right = max(left, min(host[2], round((rect['x'] + rect['width']) * sx)))
    bottom = max(top, min(host[3], round((rect['y'] + rect['height']) * sy)))
    return (host[0] + left, host[1] + top, right - left, bottom - top)


class DeepSeekPane:
    def __init__(self, window, owner_provider, profile_root, *, target=TARGET, test_origin=None):
        # A test origin is supplied only by the isolated native test harness;
        # neither URL nor filesystem locations are accepted by the HTTP API.
        if target != TARGET and (not test_origin or not target.startswith(test_origin + '/')):
            raise ValueError('Only the fixed DeepSeek origin is allowed')
        self.window, self.owner_provider = window, owner_provider
        self.profile_root, self.target, self.test_origin = Path(profile_root), target, test_origin
        self.secret = secrets.token_bytes(32)
        self.lock = threading.RLock()
        self.owner = self.active = self.view = self.panel = self.timer = None
        self.popups = []
        self.status, self.error = 'idle', None
        self.last_sequence = {}
        self.last_frame = 0
        self.closed = False
        self.attached = False
        self.shortcuts = NativeShortcuts()

    def _owner(self):
        try:
            owner = self.owner_provider()
            if not owner or len(owner) != 3 or not all(isinstance(v, (str, int)) for v in owner):
                return None
            return tuple(owner)
        except (ServiceError, RuntimeError):
            return None

    def _binding(self, owner):
        return hmac.new(self.secret, json.dumps(owner, ensure_ascii=True, separators=(',', ':')).encode(), hashlib.sha256).hexdigest()

    def snapshot(self):
        owner = self._owner()
        native = getattr(self.window, 'native', None)
        available = bool(not self.closed and owner and native is not None and not native.IsDisposed
                         and getattr(getattr(native, 'browser', None), 'webview', None) is not None)
        with self.lock:
            return {'available': available, 'ownerKey': self._binding(owner) if owner else None,
                    'sequence': self.last_sequence.get(self._binding(owner), 0) if owner else 0,
                    'status': self.status, 'errorCode': self.error,
                    'visible': bool(self.panel is not None and not self.panel.IsDisposed and self.panel.Visible)}

    def _ui(self, action):
        native = getattr(self.window, 'native', None)
        if native is None or native.IsDisposed:
            raise ServiceError(503, '原生网页尚未就绪')
        if not native.InvokeRequired:
            return action()
        from System import Action
        result, errors = [], []
        def run():
            try:
                result.append(action())
            except Exception as error:
                errors.append(error)
        native.Invoke(Action(run))
        if errors:
            raise errors[0]
        return result[0] if result else None

    def update(self, value):
        value = frame(value)
        owner = self._owner()
        if not owner or not hmac.compare_digest(value['ownerKey'], self._binding(owner)):
            raise ServiceError(409, '账号已切换，请重新打开网页')
        with self.lock:
            previous = self.last_sequence.get(value['ownerKey'], 0)
            if value['sequence'] <= previous:
                return self.snapshot()
            self.last_sequence[value['ownerKey']] = value['sequence']
            if len(self.last_sequence) > 16:
                for key in list(self.last_sequence)[:-8]:
                    del self.last_sequence[key]
        def apply():
            if self.closed or self._owner() != owner:
                self._hide()
                return
            if self.last_sequence.get(value['ownerKey']) != value['sequence']:
                return
            if not value['visible']:
                if self.active == value['viewId']:
                    self._hide()
                return
            if self.owner != owner:
                self._dispose_view()
                self.owner = owner
            if value.get('retry') and self.status == 'error':
                # Recreate a failed browser control while retaining the same
                # account profile; this also recovers a crashed renderer.
                self._dispose_view()
            self.active, self.last_frame = value['viewId'], time.monotonic()
            if self.view is None:
                self._create()
            native = self.window.native
            host = native.browser.webview
            bounds = pixel_bounds(value['rect'], value['viewport'], (host.Left, host.Top, host.ClientSize.Width, host.ClientSize.Height))
            from System.Drawing import Rectangle
            self.panel.Bounds = Rectangle(*bounds)
            self.panel.Visible = bool(bounds[2] > 0 and bounds[3] > 0 and native.Visible and str(native.WindowState) != 'Minimized' and self.status != 'error')
            if self.panel.Visible:
                self.panel.BringToFront()
                self.shortcuts.configure(value.get('shortcuts'), value['ownerKey'], value['viewId'])
            else:
                self.shortcuts.pause()
            if value.get('retry') and self.view.CoreWebView2:
                self.error, self.status = None, 'loading'
                self.view.CoreWebView2.Navigate(self.target)
        try:
            self._ui(apply)
        except ServiceError:
            raise
        except Exception:
            self.error, self.status = 'NATIVE_INITIALIZATION_FAILED', 'error'
            try:
                self._ui(self._hide)
            except Exception:
                pass
        return self.snapshot()

    def _allow_navigation(self, uri):
        try:
            parsed = urlsplit(str(uri))
            if parsed.username or parsed.password:
                return False
            if self.test_origin and str(uri).startswith(self.test_origin + '/'):
                return True
            if parsed.port not in (None, 443):
                return False
        except ValueError:
            return False
        return parsed.scheme == 'https' and (parsed.hostname == 'deepseek.com'
                 or (parsed.hostname or '').endswith('.deepseek.com')
                 or parsed.hostname in {'accounts.google.com', 'appleid.apple.com'})

    def _properties(self):
        from Microsoft.Web.WebView2.WinForms import CoreWebView2CreationProperties
        from System.IO import Directory
        from System.Security.AccessControl import (DirectorySecurity, FileSystemAccessRule, FileSystemRights,
                                                   InheritanceFlags, PropagationFlags, AccessControlType)
        from System.Security.Principal import WindowsIdentity
        directory = self.profile_root / profile_key(self.owner)
        for part in (directory, *directory.parents):
            if part.exists() and (part.is_symlink() or getattr(part.stat(), 'st_file_attributes', 0) & 0x400):
                raise ValueError('Redirected profile path')
        directory.mkdir(parents=True, exist_ok=True)
        security = DirectorySecurity()
        user = WindowsIdentity.GetCurrent().User
        security.SetAccessRuleProtection(True, False)
        security.SetOwner(user)
        security.AddAccessRule(FileSystemAccessRule(user, FileSystemRights.FullControl,
            InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
            getattr(PropagationFlags, 'None'), AccessControlType.Allow))
        Directory.SetAccessControl(str(directory), security)
        props = CoreWebView2CreationProperties()
        props.UserDataFolder, props.ProfileName = str(directory), 'ToBeDeepSeek'
        props.set_IsInPrivateModeEnabled(False)
        return props

    def _create(self):
        import System.Windows.Forms as Forms
        from Microsoft.Web.WebView2.WinForms import WebView2
        native = self.window.native
        panel, view = Forms.Panel(), WebView2()
        panel.Visible, view.Dock = False, Forms.DockStyle.Fill
        view.CreationProperties = self._properties()
        panel.Controls.Add(view)
        native.Controls.Add(panel)
        self.panel, self.view = panel, view
        self.status, self.error = 'loading', None
        def initialized(sender, args):
            if view is not self.view or view.IsDisposed:
                return
            if not args.IsSuccess:
                self.error, self.status = 'WEBVIEW2_INITIALIZATION_FAILED', 'error'
                self._hide()
                return
            try:
                self._configure(view)
                view.CoreWebView2.Navigate(self.target)
            except Exception:
                self.error, self.status = 'WEBVIEW2_CONFIGURATION_FAILED', 'error'
                self._hide()
        view.CoreWebView2InitializationCompleted += initialized
        view.EnsureCoreWebView2Async(None)
        if not self.attached:
            self.attached = True
            # Hide immediately on native bounds changes. React sends a fresh
            # clipped rectangle before the child may cover content again.
            native.Resize += lambda *_: self._hide()
            native.VisibleChanged += lambda *_: self._hide()
            native.DpiChanged += lambda *_: self._hide()
            self.timer = Forms.Timer()
            self.timer.Interval = 200
            def watch(*_):
                if self.closed or self._owner() != self.owner or time.monotonic() - self.last_frame > 3 or str(native.WindowState) == 'Minimized':
                    self._hide()
            self.timer.Tick += watch
            self.timer.Start()

    def _configure(self, view):
        core = view.CoreWebView2
        owner = self.owner
        core.Settings.AreHostObjectsAllowed = False
        core.Settings.IsWebMessageEnabled = False
        core.Settings.AreDevToolsEnabled = False
        def starting(sender, args):
            if self.closed or view.IsDisposed or self.owner != owner or self._owner() != owner or not self._allow_navigation(args.Uri):
                args.Cancel = True
                return
            if view is self.view:
                self.status, self.error = 'loading', None
        def completed(sender, args):
            if view is not self.view:
                return
            http_status = getattr(args, 'HttpStatusCode', 0)
            if args.IsSuccess and (not http_status or http_status < 400):
                self.status, self.error = 'ready', None
            else:
                self.status, self.error = 'error', 'HTTP_ERROR' if http_status >= 400 else 'NAVIGATION_FAILED'
                self._hide()
        core.NavigationStarting += starting
        core.NavigationCompleted += completed
        def failed(sender, args):
            if view is self.view and not self.closed:
                self.status, self.error = 'error', 'WEBVIEW2_PROCESS_FAILED'
                self._hide()
        core.ProcessFailed += failed
        def popup(sender, args):
            if self.closed or view.IsDisposed or self.owner != owner or self._owner() != owner:
                args.Handled = True
                return
            self._popup(sender, args)
        core.NewWindowRequested += popup
        def download(sender, args):
            args.Cancel = True
        core.DownloadStarting += download

    def _popup(self, sender, args):
        # A user-requested site login popup stays in an owned WebView2 window
        # with the same dedicated profile. No system browser or cookie import.
        args.Handled = True
        if not args.IsUserInitiated or not self._allow_navigation(args.Uri) or self.closed or self._owner() != self.owner or len(self.popups) >= 2:
            return
        import System.Windows.Forms as Forms
        from Microsoft.Web.WebView2.WinForms import WebView2
        popup, view = Forms.Form(), WebView2()
        popup.Text, popup.Width, popup.Height = 'DeepSeek', 560, 720
        popup.StartPosition = Forms.FormStartPosition.CenterParent
        view.Dock, view.CreationProperties = Forms.DockStyle.Fill, self._properties()
        popup.Controls.Add(view)
        deferral = args.GetDeferral()
        owner = self.owner
        self.popups.append(popup)
        def initialized(sender, event):
            try:
                if event.IsSuccess and not popup.IsDisposed and self._owner() == owner:
                    self._configure(view)
                    args.NewWindow = view.CoreWebView2
                else:
                    popup.Close()
            finally:
                deferral.Complete()
        view.CoreWebView2InitializationCompleted += initialized
        popup.FormClosed += lambda *_: self.popups.remove(popup) if popup in self.popups else None
        popup.Show(self.window.native)
        view.EnsureCoreWebView2Async(None)

    def _hide(self):
        self.shortcuts.pause()
        if self.panel is not None and not self.panel.IsDisposed:
            self.panel.Visible = False
        for popup in list(self.popups):
            if not popup.IsDisposed:
                popup.Close()

    def _dispose_view(self):
        self._hide()
        if self.panel is not None and not self.panel.IsDisposed:
            self.window.native.Controls.Remove(self.panel)
            self.panel.Dispose()
        self.panel = self.view = None
        self.status, self.error = 'idle', None

    def close(self):
        if self.closed:
            return
        self.closed = True
        def dispose():
            if self.timer is not None:
                self.timer.Stop()
                self.timer.Dispose()
                self.timer = None
            self._dispose_view()
        try:
            self._ui(dispose)
        except (ServiceError, RuntimeError):
            pass

    def shortcut_snapshot(self):
        owner = self._owner()
        binding = self._binding(owner) if owner else None
        return self.shortcuts.snapshot(binding) | {'ownerKey': binding}


def bind(server, window, profile_root):
    def owner():
        accounts = getattr(server, 'accounts', None)
        if accounts is not None:
            accounts.require()
            session = accounts.session
            if session is None:
                raise ServiceError(401, '请先登录账号')
            return session['endpoint'], session['userId'], accounts.restore_epoch
        training = server.browser_account_context()
        profile = training._ranking_profile()
        return profile['endpoint'], profile['user_id'], id(training)
    pane = DeepSeekPane(window, owner, profile_root)
    server.embedded_deepseek = pane
    return pane
