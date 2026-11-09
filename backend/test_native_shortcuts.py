import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
from native_shortcuts import NativeShortcuts, combination, validate_registration, windows_combination
from training import ServiceError


class NativeShortcutTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.
        self.shortcuts = NativeShortcuts(clock=lambda: self.now)
        self.registration = {'serial': 1, 'bindings': [
            {'route': 'workbench', 'id': 'workbench-next', 'combo': 'Ctrl+ArrowRight', 'context': 'problem-A'},
            {'route': 'workbench', 'id': 'run', 'combo': 'Ctrl+R', 'context': 'problem-A'},
            {'route': 'workbench', 'id': 'toolbar-lock', 'combo': 'Alt+T', 'context': 'problem-A'},
            {'route': 'study', 'id': 'study-toolbar-lock', 'combo': 'Alt+Shift+T', 'context': 'problem-A'},
            {'route': 'app', 'id': 'desktop-fullscreen', 'combo': 'F11', 'context': 'problem-A'}]}
        self.shortcuts.configure(self.registration, 'owner-A', 'view-A')

    def test_existing_combinations_and_custom_symbols_match_browser_normalization(self):
        for key, modifiers, expected in [
                (39, {'control': True}, 'ctrl+arrowright'), (84, {'alt': True}, 'alt+t'),
                (84, {'alt': True, 'shift': True}, 'alt+shift+t'),
                (13, {'control': True, 'shift': True}, 'ctrl+shift+enter'),
                (188, {'control': True}, 'ctrl+,'), (220, {'control': True}, 'ctrl+\\'),
                (191, {'control': True, 'shift': True}, 'ctrl+?'),
                (187, {'control': True, 'shift': True}, 'ctrl++'), (122, {}, 'f11')]:
            with self.subTest(expected=expected):
                self.assertEqual(windows_combination(key, **modifiers), expected)
        self.assertIsNone(windows_combination(65))
        self.assertIsNone(windows_combination(39))
        self.assertIsNone(windows_combination(82, control=True, meta=True))
        for value in ('U', '?', 'ArrowRight', 'Ctrl+', 'Ctrl+Ctrl+R', 'Ctrl+not-an-editing-key'):
            self.assertIsNone(combination(value))

    def test_only_a_registered_physical_combination_in_this_native_child_is_queued(self):
        key = self.shortcuts.key
        self.assertFalse(key(39, 0, child_owned=False, control=True))
        self.assertFalse(key(39, 16, child_owned=True, control=True))
        self.assertFalse(key(39, 2, child_owned=True, control=True))
        self.assertFalse(key(65, 0, child_owned=True))
        self.assertFalse(key(39, 0, child_owned=True))
        self.assertFalse(key(82, 0, child_owned=True, control=True, shift=True))
        self.assertFalse(self.shortcuts.snapshot('owner-A')['actions'])
        self.assertTrue(key(39, 0, child_owned=True, control=True))
        snapshot = self.shortcuts.snapshot('owner-A')
        self.assertEqual([(event['route'], event['id']) for event in snapshot['actions']], [('workbench', 'workbench-next')])
        self.assertEqual(set(snapshot['actions'][0]), {'route', 'id', 'sequence', 'ageSeconds'})

    def test_auto_repeat_and_redraw_cannot_repeat_the_action_until_real_key_up(self):
        for _ in range(12):
            self.assertTrue(self.shortcuts.key(39, 0, child_owned=True, control=True))
        self.assertEqual(len(self.shortcuts.snapshot('owner-A')['actions']), 1)
        self.shortcuts.pause()
        self.shortcuts.configure({**self.registration, 'serial': 2}, 'owner-A', 'view-A')
        self.assertTrue(self.shortcuts.key(39, 0, child_owned=True, control=True))
        self.assertFalse(self.shortcuts.snapshot('owner-A')['actions'])
        self.assertFalse(self.shortcuts.key(39, 128, child_owned=False, control=True))
        self.assertTrue(self.shortcuts.key(39, 0, child_owned=True, control=True))
        self.assertEqual(len(self.shortcuts.snapshot('owner-A')['actions']), 1)

    def test_owner_context_expiry_and_hidden_pane_reject_old_actions(self):
        self.shortcuts.key(82, 0, child_owned=True, control=True)
        self.assertFalse(self.shortcuts.snapshot('owner-B')['actions'])
        self.now += 2.1
        self.assertFalse(self.shortcuts.snapshot('owner-A')['actions'])
        self.shortcuts.pause()
        self.assertFalse(self.shortcuts.key(122, 0, child_owned=True))
        self.assertFalse(self.shortcuts.snapshot('owner-A')['available'])

    def test_first_registered_route_wins_and_account_overrides_replace_defaults(self):
        custom = {'serial': 2, 'bindings': [
            {'route': 'editor', 'id': 'run', 'combo': 'Ctrl+J', 'context': 'A'},
            {'route': 'lower', 'id': 'refresh', 'combo': 'Ctrl+J', 'context': 'A'}]}
        self.shortcuts.configure(custom, 'owner-A', 'view-A')
        self.assertFalse(self.shortcuts.key(82, 0, child_owned=True, control=True))
        self.assertTrue(self.shortcuts.key(74, 0, child_owned=True, control=True))
        self.assertEqual(self.shortcuts.snapshot('owner-A')['actions'][0]['route'], 'editor')

    def test_registration_has_no_action_setter_or_arbitrary_webpage_input(self):
        for invalid in ({'serial': 1, 'bindings': [], 'enqueue': {'id': 'run'}},
                        {'serial': True, 'bindings': []},
                        {'serial': 1, 'bindings': [{**self.registration['bindings'][0], 'combo': 'A'}]},
                        {'serial': 1, 'bindings': [{**self.registration['bindings'][0], 'url': 'https://example.com'}]}):
            with self.subTest(value=invalid), self.assertRaises(ServiceError):
                validate_registration(invalid)


if __name__ == '__main__':
    unittest.main()
