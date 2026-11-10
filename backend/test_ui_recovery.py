"""Isolated native failure and visibility regressions; no live view or state."""
import sys
import types
import unittest
from unittest.mock import Mock, patch
from webview_resources import MainViewResources


class MainViewRecoveryTests(unittest.TestCase):
    def test_renderer_exit_recovers_twice_then_offers_manual_recovery(self):
        policy = MainViewResources(Mock())
        policy.core = Mock()
        policy._show_failure = Mock()
        with self.assertLogs('tb.desktop.resources', level='ERROR'):
            for _ in range(3):
                policy._process_failed(None, types.SimpleNamespace(ProcessFailedKind='RenderProcessExited'))
        self.assertEqual(policy.core.Reload.call_count, 2)
        policy._show_failure.assert_called_once_with(retry=True)
        self.assertFalse(policy.frontend_alive())
        policy._navigation_completed(None,types.SimpleNamespace(IsSuccess=False))
        self.assertFalse(policy.frontend_alive())
        policy._navigation_completed(None,types.SimpleNamespace(IsSuccess=True))
        self.assertTrue(policy.frontend_alive())

    def test_gpu_and_slow_renderer_do_not_reload_unsaved_session(self):
        policy = MainViewResources(Mock())
        policy.core = Mock()
        policy._show_failure = Mock()
        with self.assertLogs('tb.desktop.resources', level='ERROR'):
            for kind in ('GpuProcessExited', 'RenderProcessUnresponsive'):
                policy._process_failed(None, types.SimpleNamespace(ProcessFailedKind=kind))
        policy.core.Reload.assert_not_called()
        policy._show_failure.assert_not_called()
        self.assertTrue(policy.frontend_alive())

    def test_browser_exit_notifies_pending_close_and_cannot_be_cleared_by_navigation(self):
        policy=MainViewResources(Mock());policy.core=Mock();policy._show_failure=Mock()
        policy.on_frontend_failed=Mock()
        event=types.SimpleNamespace(ProcessFailedKind='BrowserProcessExited',Reason='Unexpected',ExitCode=23)
        with self.assertLogs('tb.desktop.resources',level='ERROR') as messages:
            policy._process_failed(None,event)
        self.assertIn('reason=Unexpected; exit_code=23',messages.output[0])
        self.assertFalse(policy.frontend_alive());policy.on_frontend_failed.assert_called_once()
        policy._show_failure.assert_called_once_with(retry=False)
        policy._navigation_completed(None,types.SimpleNamespace(IsSuccess=True))
        self.assertFalse(policy.frontend_alive())

    def test_optional_dotnet_diagnostic_getters_cannot_block_native_close(self):
        class PartialSdkEvent:
            ProcessFailedKind='BrowserProcessExited'
            @property
            def Reason(self):raise RuntimeError('SDK getter unavailable')
            @property
            def ExitCode(self):raise RuntimeError('SDK getter unavailable')
        policy=MainViewResources(Mock());policy._show_failure=Mock()
        policy.on_frontend_failed=Mock()
        with self.assertLogs('tb.desktop.resources',level='ERROR'):
            policy._process_failed(None,PartialSdkEvent())
        self.assertFalse(policy.frontend_alive());policy.on_frontend_failed.assert_called_once()

    def test_minimize_restore_keeps_overlay_visibility_owned_by_overlay(self):
        forms = types.ModuleType('System.Windows.Forms')
        forms.FormWindowState = types.SimpleNamespace(Minimized='minimized')
        policy = MainViewResources(Mock())
        policy.form = types.SimpleNamespace(WindowState='minimized', Visible=True)
        policy.view = types.SimpleNamespace(IsDisposed=False, Visible=True)
        policy.core = Mock()
        policy.memory_supported = False
        with patch.dict(sys.modules, {'System.Windows.Forms': forms}):
            policy._apply()
            self.assertTrue(policy.view.Visible)
            policy.form.WindowState = 'normal'
            policy._apply()
            self.assertTrue(policy.view.Visible)
            policy.view.Visible = False
            policy._apply()
            self.assertFalse(policy.view.Visible)
