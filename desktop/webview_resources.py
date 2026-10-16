"""Reduce main-window WebView work without suspending scripts or submissions.

Only the TB frontend view is managed. Original-site views keep their request,
response, cookie and navigation handlers. All native changes run on the UI
thread and optional SDK capabilities are allowed to fail without blocking TB.
"""
from __future__ import annotations

import logging

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
        self._apply()

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
            from System.Windows.Forms import DockStyle, FormWindowState
            minimized = self.form.WindowState == FormWindowState.Minimized
            if minimized and self.view.Visible:
                self.hidden_for_minimize = True
                self.view.Visible = False
            elif not minimized and self.hidden_for_minimize:
                # An original-site overlay may have opened while minimized.
                # Leave that overlay in control of restoring the editor view.
                overlay_visible = any(control != self.view and control.Visible and control.Dock == DockStyle.Fill
                                      for control in self.form.Controls)
                self.hidden_for_minimize = False
                if not overlay_visible:
                    self.view.Visible = True
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
