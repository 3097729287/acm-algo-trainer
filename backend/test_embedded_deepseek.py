"""Native-pane ownership, geometry and message boundaries; no browser starts."""
import copy
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
import test_training as fixtures

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
from native_activity import NativeActivity, physical_input
from embedded_deepseek import DeepSeekPane, frame, pixel_bounds, profile_key
from training import ServiceError


class EmbeddedDeepSeekTests(unittest.TestCase):
    def setUp(self):
        self.owner = ('https://service.example', 'test-owner-A', 1)
        native = SimpleNamespace(IsDisposed=False, browser=SimpleNamespace(webview=object()))
        self.pane = DeepSeekPane(SimpleNamespace(native=native), lambda: self.owner, Path('unused-test-profile'))
        self.pane._ui = lambda action: action()

    def message(self, **changes):
        return {'viewId': 'a' * 32, 'sequence': 1, 'ownerKey': self.pane.snapshot()['ownerKey'],
                'visible': False, **changes}

    def test_profile_survives_session_epoch_but_isolated_from_other_owner_and_service(self):
        key = profile_key(self.owner)
        self.assertEqual(profile_key((*self.owner[:2], 99)), key)
        self.assertNotEqual(profile_key((self.owner[0], 'test-owner-B', 1)), key)
        self.assertNotEqual(profile_key(('https://another.example', self.owner[1], 1)), key)
        self.assertRegex(key, '^[a-f0-9]{64}$')

    def test_native_binding_rejects_old_session_even_for_same_profile(self):
        stale = self.message()
        self.owner = (*self.owner[:2], 2)
        with self.assertRaises(ServiceError) as issue:
            self.pane.update(stale)
        self.assertEqual(issue.exception.status, 409)
        self.assertFalse(self.pane.last_sequence)

    def test_old_owner_cannot_control_new_account(self):
        stale = self.message()
        self.owner = (self.owner[0], 'test-owner-B', 1)
        with self.assertRaises(ServiceError):
            self.pane.update(stale)

    def test_reordered_requests_cannot_override_a_newer_visibility_message(self):
        first = self.message(sequence=2)
        self.pane.update(first)
        self.pane._ui = lambda action: self.fail('Stale geometry must not touch native controls')
        self.pane.update(self.message(sequence=1))
        self.assertEqual(self.pane.last_sequence[first['ownerKey']], 2)

    def test_hidden_old_tab_cannot_hide_the_active_other_tab(self):
        self.pane.active = 'b' * 32
        self.pane._hide = lambda: self.fail('An unrelated hidden tab must not hide the active one')
        self.pane.update(self.message())

    def test_frontend_cannot_supply_url_profile_path_owner_or_source_text(self):
        for field in ('url', 'path', 'profile', 'owner', 'code', 'markdown', 'cookie'):
            with self.subTest(field=field), self.assertRaises(ServiceError):
                frame(self.message(**{field: 'untrusted'}))

    def test_nonfinite_negative_oversized_and_boolean_geometry_rejected(self):
        valid = self.message(visible=True, rect={'x': 10, 'y': 20, 'width': 490, 'height': 600},
                             viewport={'width': 1000, 'height': 800})
        self.assertEqual(frame(valid), valid)
        for key, value in [('x', -1), ('width', float('nan')), ('height', float('inf')),
                           ('width', True), ('height', 40000), ('x', 800)]:
            changed = copy.deepcopy(valid)
            changed['rect'][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ServiceError):
                frame(changed)

    def test_host_client_pixel_mapping_accounts_for_dpi_and_zoom_without_crossing_code(self):
        rect = {'x': 0, 'y': 44, 'width': 600, 'height': 756}
        viewport = {'width': 1200, 'height': 800}
        self.assertEqual(pixel_bounds(rect, viewport, (0, 0, 1800, 1200)), (0, 66, 900, 1134))
        self.assertEqual(pixel_bounds(rect, viewport, (3, 4, 2400, 1600)), (3, 92, 1200, 1512))
        self.assertEqual(pixel_bounds(rect, viewport, (0, 0, 960, 640)), (0, 35, 480, 605))

    def test_navigation_is_deepseek_or_its_interactive_sign_in_providers_only(self):
        for url in ('https://chat.deepseek.com/', 'https://chat.deepseek.com/sign_in',
                    'https://accounts.google.com/o/oauth2/auth', 'https://appleid.apple.com/auth/authorize'):
            self.assertTrue(self.pane._allow_navigation(url))
        for url in ('http://chat.deepseek.com/', 'file:///C:/private', 'https://deepseek.com.evil.test/',
                    'http://127.0.0.1:18765/api/data', 'https://unrelated.example/',
                    'https://user:password@chat.deepseek.com/', 'https://chat.deepseek.com:9999/',
                    'https://chat.deepseek.com:invalid/', 'https://['):
            self.assertFalse(self.pane._allow_navigation(url))


class EmbeddedDeepSeekHTTPTests(unittest.TestCase):
    setUp = fixtures.HTTPTests.setUp
    tearDown = fixtures.HTTPTests.tearDown
    request = fixtures.HTTPTests.request

    def test_existing_local_token_guard_precedes_native_control_and_frames_reject_paths(self):
        current = [('https://example.test', 'temporary-owner-A', 1)]
        window = SimpleNamespace(native=SimpleNamespace(IsDisposed=False, browser=SimpleNamespace(webview=object())))
        pane = DeepSeekPane(window, lambda: current[0], self.root / 'dedicated-profile')
        pane._ui = lambda action: action()
        self.server.embedded_deepseek = pane
        status, state = self.request('GET', '/api/desktop/deepseek')
        self.assertEqual(status, 200)
        body = {'ownerKey': state['ownerKey'], 'viewId': 'a' * 32, 'sequence': 1, 'visible': False}
        status, _ = self.request('POST', '/api/desktop/deepseek', body, token='untrusted')
        self.assertEqual(status, 403)
        self.assertFalse(pane.last_sequence)
        status, _ = self.request('POST', '/api/desktop/deepseek', {**body, 'profile': 'arbitrary-path'})
        self.assertEqual(status, 400)
        self.assertFalse((self.root / 'dedicated-profile').exists())
        status, _ = self.request('POST', '/api/desktop/deepseek', body)
        self.assertEqual(status, 200)
        current[0] = (current[0][0], 'temporary-owner-B', 2)
        status, _ = self.request('POST', '/api/desktop/deepseek', {**body, 'sequence': 2})
        self.assertEqual(status, 409)

    def test_native_input_snapshot_is_guarded_read_only_and_never_accepts_page_events(self):
        activity = NativeActivity(clock=lambda: 100.)
        self.server.native_activity = activity
        status, initial = self.request('GET', '/api/desktop/input-activity')
        self.assertEqual(status, 200)
        self.assertFalse(initial['observed'])
        status, _ = self.request('POST', '/api/desktop/input-activity', {'revision': 999}, token='untrusted')
        self.assertEqual(status, 403)
        status, _ = self.request('POST', '/api/desktop/input-activity', {'revision': 999})
        self.assertEqual(status, 404)
        status, _ = self.request('POST', '/api/desktop/deepseek-shortcuts', {'id': 'run', 'enqueue': True})
        self.assertEqual(status, 404)
        self.assertEqual(activity.snapshot(), initial)


class NativeActivityTests(unittest.TestCase):
    def test_only_non_injected_input_owned_by_this_window_is_accepted(self):
        for kind in ('mouse', 'keyboard'):
            self.assertTrue(physical_input(kind, 0, True))
            self.assertFalse(physical_input(kind, 0, False))
        for flags in (1, 2, 3):
            self.assertFalse(physical_input('mouse', flags, True))
        for flags in (2, 16, 18, 146):
            self.assertFalse(physical_input('keyboard', flags, True))
        self.assertTrue(physical_input('keyboard', 128, True))  # physical key-up
        for kind in ('focus', 'navigation', 'poll', 'page-message', 'touch-js'):
            self.assertFalse(physical_input(kind, 0, True))

    def test_polling_preserves_revision_and_uses_age_of_last_actual_input(self):
        clock = [100.]
        activity = NativeActivity(clock=lambda: clock[0])
        initial = activity.snapshot()
        self.assertIsNone(initial['ageSeconds'])
        clock[0] += 20
        activity._observe('mouse', 1, True)
        activity._observe('keyboard', 0, False)
        self.assertEqual(activity.snapshot(), initial)
        activity._observe('keyboard', 0, True)
        first = activity.snapshot()
        self.assertEqual(first['revision'], 1)
        self.assertTrue(first['observed'])
        self.assertEqual(first['ageSeconds'], 0)
        clock[0] += 301
        later = activity.snapshot()
        self.assertEqual(later['revision'], first['revision'])
        self.assertEqual(later['ageSeconds'], 301)
        self.assertEqual(later['session'], first['session'])
        self.assertEqual(set(later), {'available', 'session', 'revision', 'observed', 'ageSeconds'})
        self.assertNotEqual(NativeActivity().snapshot()['session'], first['session'])
        activity.close()
        activity._observe('mouse', 0, True)
        self.assertEqual(activity.snapshot()['revision'], 1)


if __name__ == '__main__':
    unittest.main()
