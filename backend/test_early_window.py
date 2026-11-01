import json
from pathlib import Path
import tempfile
import time
import unittest
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from early_window import EarlyWindow
import test_training as fixtures

class EarlyWindowTests(unittest.TestCase):
    def test_real_ui_is_immediate_and_pending_backend_cannot_accept_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'index.html').write_text('<main>Real built interface</main>','utf8')
            host=EarlyWindow(root,resume_expected=True)
            try:
                start=time.perf_counter()
                self.assertIn(b'Real built interface',urlopen(host.url).read())
                self.assertLess(time.perf_counter()-start,.2)
                value=json.load(urlopen(host.url+'/api/account?background=1'))
                self.assertFalse(value['authenticated']);self.assertTrue(value['restoring'])
                with self.assertRaises(HTTPError) as error:urlopen(Request(host.url+'/api/account/login',data=b'{}',headers={'X-TB-Token':'forged'}))
                self.assertEqual(error.exception.code,503);error.exception.close()
                with self.assertRaises(HTTPError) as error:urlopen(Request(host.url+'/',headers={'Host':'evil.invalid'}))
                self.assertEqual(error.exception.code,403);error.exception.close()
                host.fail();value=json.load(urlopen(host.url+'/api/account?background=1'))
                self.assertFalse(value['restoring']);self.assertTrue(value['error'])
            finally:host.close()

    def test_forwarding_preserves_the_normal_token_and_origin_guards(self):
        fixture=fixtures.HTTPTests();fixture.setUp()
        with tempfile.TemporaryDirectory() as directory:
            Path(directory,'index.html').write_text('Fixture','utf8');host=EarlyWindow(directory)
            try:
                host.activate(fixture.server)
                account=json.load(urlopen(host.url+'/api/account?background=1'))
                self.assertFalse(account['required'])
                with self.assertRaises(HTTPError) as error:urlopen(Request(host.url+'/api/draft',data=b'{}',headers={'Content-Type':'application/json'}))
                self.assertEqual(error.exception.code,403);error.exception.close()
                with self.assertRaises(HTTPError) as error:urlopen(Request(host.url+'/api/draft',data=b'{}',headers={'Origin':'https://evil.invalid','Content-Type':'application/json','X-TB-Token':account['token']}))
                self.assertEqual(error.exception.code,403);error.exception.close()
                self.assertIn('training',json.load(urlopen(host.url+'/api/workspace')))
            finally:host.close();fixture.tearDown()
