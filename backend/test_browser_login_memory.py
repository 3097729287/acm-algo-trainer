"""Encrypted remembered login never reads another browser profile."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
from browser_login_memory import BrowserLoginMemory
from persistence import load_document


class Page:
    def __init__(self, cookies): self.cookies, self.set = cookies, []
    def call(self, method, params=None):
        if method == 'Storage.getCookies': return {'cookies': self.cookies}
        if method == 'Storage.setCookies': self.set.extend(params['cookies']); return {}
        raise AssertionError(method)


class LoginMemoryTests(unittest.TestCase):
    def test_session_cookie_survives_restart_but_stays_encrypted_and_site_scoped(self):
        with tempfile.TemporaryDirectory(prefix='tb-managed-login-') as directory:
            cookie = dict(name='fixture-session', value='fixture-secret-do-not-log', domain='.nowcoder.com', path='/', secure=True, httpOnly=True, expires=-1)
            current = Page([cookie, dict(cookie, domain='.unrelated.example')])
            saved = BrowserLoginMemory(directory)
            saved.capture(current)
            self.assertNotIn(cookie['value'], load_document(saved.path, ''))
            resumed, restored = BrowserLoginMemory(directory), Page([])
            resumed.restore(restored)
            self.assertEqual(len(restored.set), 1)
            self.assertEqual(restored.set[0]['value'], cookie['value'])
            self.assertNotIn('expires', restored.set[0])
            resumed.capture(Page([]))  # Explicit site logout must remain logged out.
            empty = Page([])
            BrowserLoginMemory(directory).restore(empty)
            self.assertEqual(empty.set, [])

    def test_existing_cookies_are_not_overwritten_and_expired_sessions_are_not_restored(self):
        with tempfile.TemporaryDirectory(prefix='tb-managed-login-') as directory:
            cookie = dict(name='session', value='old-fixture', domain='atcoder.jp', path='/')
            memory = BrowserLoginMemory(directory)
            memory.capture(Page([cookie]))
            page = Page([dict(cookie, value='new-fixture')])
            memory.restore(page)
            self.assertEqual(page.set, [])
            with patch('browser_login_memory.time.time', return_value=10**12):
                memory.restore(page := Page([]))
            self.assertEqual(page.set, [])
