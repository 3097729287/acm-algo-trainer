"""A native close waits for local save, never for cloud traffic."""
import sys
from pathlib import Path
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
from close_coordinator import CloseCoordinator,SAVE_AND_CLOSE

class CloseTests(unittest.TestCase):
    def test_close_waits_for_confirmed_local_save_and_failure_keeps_window(self):
        window=Mock();stop=Mock();close=CloseCoordinator(window,stop)
        self.assertFalse(close.on_closing())
        close.saver.join(1)
        window.evaluate_js.assert_called_once_with(SAVE_AND_CLOSE.replace('__TB_CLOSE_REQUEST__','1'))
        self.assertFalse(close.on_closing())
        close.saver.join(1)
        close.desktop_close_ready(False,close.request_id)
        window.destroy.assert_not_called();stop.assert_not_called()
        self.assertFalse(close.on_closing())
        with patch('close_coordinator.threading.Timer') as timer:
            close.desktop_close_ready(True,close.request_id)
            timer.assert_called_once_with(.05,window.destroy)
            timer.return_value.start.assert_called_once()
        self.assertTrue(close.on_closing());stop.assert_called_once()

    def test_missing_frontend_does_not_silently_discard_a_pending_draft(self):
        window=Mock();window.evaluate_js.side_effect=RuntimeError('not ready')
        close=CloseCoordinator(window)
        self.assertFalse(close.on_closing())
        close.saver.join(1)
        self.assertFalse(close.requesting)
        window.destroy.assert_not_called()

    def test_startup_can_close_before_any_editor_or_js_bridge_has_loaded(self):
        window=Mock();window.events.loaded.is_set.return_value=False
        stop=Mock();close=CloseCoordinator(window,stop)
        self.assertTrue(close.on_closing())
        stop.assert_called_once();window.evaluate_js.assert_not_called()

    def test_exited_browser_can_close_without_a_javascript_save(self):
        window=Mock();stop=Mock()
        close=CloseCoordinator(window,stop,frontend_alive=lambda:False)
        self.assertTrue(close.on_closing())
        self.assertTrue(close.on_closing())
        window.evaluate_js.assert_not_called();stop.assert_called_once()

    def test_process_exit_finishes_pending_close_without_accepting_late_save(self):
        window=Mock();stop=Mock();close=CloseCoordinator(window,stop)
        self.assertFalse(close.on_closing());close.saver.join(1)
        old_request=close.request_id
        with patch('close_coordinator.threading.Timer') as timer:
            close.frontend_failed()
            close.frontend_failed()
            close.desktop_close_ready(False,old_request)
            timer.assert_called_once_with(.05,window.destroy)
        self.assertTrue(close.approved)
        self.assertFalse(close.requesting)
        self.assertTrue(close.on_closing());stop.assert_called_once()

    def test_late_callback_cannot_approve_a_later_close_request(self):
        window=Mock();stop=Mock();close=CloseCoordinator(window,stop)
        self.assertFalse(close.on_closing());close.saver.join(1)
        old_request=close.request_id
        close.desktop_close_ready(False,old_request)
        self.assertFalse(close.on_closing());close.saver.join(1)
        new_request=close.request_id
        with patch('close_coordinator.threading.Timer') as timer:
            close.desktop_close_ready(True,old_request)
            close.desktop_close_ready(True)
            timer.assert_not_called()
            self.assertTrue(close.requesting)
            close.desktop_close_ready(True,new_request)
            timer.assert_called_once()

    def test_failure_without_close_intent_does_not_close_or_approve_window(self):
        window=Mock();close=CloseCoordinator(window)
        close.frontend_failed()
        self.assertFalse(close.approved);window.destroy.assert_not_called()

    def test_unknown_health_does_not_bypass_failed_save(self):
        window=Mock();probe=Mock(side_effect=RuntimeError('optional SDK'))
        close=CloseCoordinator(window,frontend_alive=probe)
        self.assertFalse(close.on_closing());close.saver.join(1)
        close.desktop_close_ready(False,close.request_id)
        self.assertFalse(close.approved);window.destroy.assert_not_called()

    def test_cleanup_failure_does_not_cancel_native_close(self):
        window=Mock();stop=Mock(side_effect=RuntimeError('cleanup failed'))
        close=CloseCoordinator(window,stop,frontend_alive=lambda:False)
        with self.assertLogs('tb.desktop',level='ERROR'):
            self.assertTrue(close.on_closing())
        self.assertTrue(close.on_closing());stop.assert_called_once()

if __name__=='__main__':unittest.main()
