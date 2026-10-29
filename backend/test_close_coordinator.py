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
        window.evaluate_js.assert_called_once_with(SAVE_AND_CLOSE)
        self.assertFalse(close.on_closing())
        close.saver.join(1)
        close.desktop_close_ready(False)
        window.destroy.assert_not_called();stop.assert_not_called()
        self.assertFalse(close.on_closing())
        with patch('close_coordinator.threading.Timer') as timer:
            close.desktop_close_ready(True)
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

if __name__=='__main__':unittest.main()
