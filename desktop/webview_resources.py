"""Reduce main-window WebView work without suspending scripts or submissions.

Only the TB frontend view is managed. Original-site views keep their request,
response, cookie and navigation handlers. All native changes run on the UI
thread and optional SDK capabilities are allowed to fail without blocking TB.
"""
from __future__ import annotations

import logging
import time

LOG = logging.getLogger('tb.desktop.resources')


def _has_listeners(window, event_name):
    try:
        return len(getattr(window.events, event_name)) > 0
    except (AttributeError, TypeError):
        return True  # Unknown wrappers must retain their event behavior.


def remove_unused_network_hooks(window, browser, core):
    """Detach only pywebview's known, unused main-view header conversions.

    pywebview 6.2.1 attaches both handlers and an all-resource request filter
    even when neither Python event has listeners. TB uses its HTTP API, not
    these events. Native original-site interceptors are never touched.
    """
    removed = []
    if type(browser).__module__ != 'webview.platforms.edgechromium':
        return removed
    if not _has_listeners(window, 'request_sent'):
        try:
            from Microsoft.Web.WebView2.Core import CoreWebView2WebResourceContext
            core.WebResourceRequested -= browser.on_web_resource_request
            core.RemoveWebResourceRequestedFilter('*', CoreWebView2WebResourceContext.All)
            removed.append('request_sent')
        except Exception as issue:
            LOG.debug('Keeping main-view request compatibility: %s', type(issue).__name__)
    if not _has_listeners(window, 'response_received'):
        try:
            core.WebResourceResponseReceived -= browser.on_web_resource_response
            removed.append('response_received')
        except Exception as issue:
            LOG.debug('Keeping main-view response compatibility: %s', type(issue).__name__)
    return removed


class MainViewResources:
    def __init__(self, window):
        self.window = window
        self.form = self.view = self.core = None
        self.active = False
        self.hidden_for_minimize = False
        self.memory_supported = None
        self.memory_target = None
        self.removed_hooks = []
        self.recoveries = []
        self.failure_panel = None

    def attach(self):
        try:
            self.form = self.window.native
            browser = self.form.browser
            self.view = browser.webview
            self.active = bool(self.form.ContainsFocus)
            self.form.Activated += self._activated
            self.form.Deactivate += self._deactivated
            self.form.Resize += self._changed
            self.form.VisibleChanged += self._changed
            self.view.CoreWebView2InitializationCompleted += self._initialized
            if self.view.CoreWebView2 is not None:
                self._initialized(self.view, None)
        except Exception as issue:
            LOG.info('Native resource hints unavailable: %s', type(issue).__name__)

    def _initialized(self, _sender, event):
        if event is not None and not event.IsSuccess:
            return
        if self.core is not None:
            return
        self.core = self.view.CoreWebView2
        self.removed_hooks = remove_unused_network_hooks(self.window, self.form.browser, self.core)
        try:
            self.core.ProcessFailed += self._process_failed
        except Exception as issue:
            LOG.info('WebView recovery hook unavailable: %s', type(issue).__name__)
        self._apply()

    def _process_failed(self, _sender, event):
        kind = str(event.ProcessFailedKind)
        LOG.error('Main WebView process failure: %s', kind)
        # Reload only after an actual renderer exit, never on a slow script or
        # GPU restart. Drafts are journaled synchronously on every edit.
        if kind == 'RenderProcessExited':
            now = time.monotonic()
            self.recoveries = [stamp for stamp in self.recoveries if now - stamp < 60]
            if len(self.recoveries) < 2:
                self.recoveries.append(now)
                try:
                    self.core.Reload()
                    return
                except Exception as issue:
                    LOG.error('WebView reload failed: %s', type(issue).__name__)
            self._show_failure(retry=True)
        elif kind == 'BrowserProcessExited':
            self._show_failure(retry=False)

    def _show_failure(self, retry):
        # A native fallback also works when no JavaScript engine remains alive.
        try:
            from System.Windows.Forms import Button, DockStyle, FlowLayoutPanel, Label
            from System.Drawing import Color
            if self.failure_panel is not None:
                self.failure_panel.Dispose()
            panel = FlowLayoutPanel()
            panel.Dock = DockStyle.Fill
            panel.BackColor = Color.FromArgb(24, 28, 34)
            panel.ForeColor = Color.FromArgb(225, 229, 235)
            label = Label()
            label.AutoSize = True
            label.Text = '界面进程意外退出，请恢复界面。' if retry else '界面进程意外退出，请关闭并重新打开 ToBe。'
            panel.Controls.Add(label)
            if retry:
                button = Button()
                button.AutoSize = True
                button.Text = '恢复界面'
                def restore(_sender, _event):
                    try:
                        self.core.Reload()
                        panel.Dispose()
                        self.failure_panel = None
                        self.view.Visible = True
                    except Exception as issue:
                        LOG.error('Manual WebView reload failed: %s', type(issue).__name__)
                button.Click += restore
                panel.Controls.Add(button)
            self.failure_panel = panel
            self.form.Controls.Add(panel)
            panel.BringToFront()
        except Exception as issue:
            LOG.error('Native recovery UI failed: %s', type(issue).__name__)

    def _activated(self, _sender, _event):
        self.active = True
        self._apply()

    def _deactivated(self, _sender, _event):
        self.active = False
        self._apply()

    def _changed(self, _sender, _event):
        self._apply()

    def _apply(self):
        if self.core is None or self.view is None or self.view.IsDisposed:
            return
        try:
            from System.Windows.Forms import FormWindowState
            minimized = self.form.WindowState == FormWindowState.Minimized
            # Keep visibility owned by the original-site overlay. Toggling it
            # during minimize/restore races with WinForms visibility events and
            # can leave a restored window black. Memory hints are sufficient.
            low = minimized or not self.form.Visible or not self.active
            target = 'Low' if low else 'Normal'
            if self.memory_supported is False or target == self.memory_target:
                return
            try:
                from Microsoft.Web.WebView2.Core import CoreWebView2MemoryUsageTargetLevel
                self.core.MemoryUsageTargetLevel = getattr(CoreWebView2MemoryUsageTargetLevel, target)
                self.memory_supported = True
                self.memory_target = target
            except Exception as issue:
                self.memory_supported = False
                LOG.info('WebView memory hint unavailable; normal runtime behavior retained: %s', type(issue).__name__)
        except Exception as issue:
            LOG.debug('Main-view resource state update skipped: %s', type(issue).__name__)


def bind(window):
    """Bind once before webview.start; callbacks keep the policy alive."""
    policy = MainViewResources(window)
    window.events.before_show += policy.attach
    return policy
