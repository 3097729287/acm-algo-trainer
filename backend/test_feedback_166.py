"""Transport recovery and profile refresh; all network calls are isolated."""
import base64
import datetime as dt
import hashlib
from pathlib import Path
import ssl
import struct
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock,patch
from urllib.error import HTTPError,URLError
import zlib

from integrations import PublicClient
from leaderboard import LeaderboardClient
from external_browser import BrowserProcess,ExternalBrowserBridge

class AtCoderRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='tb-166-http-')
        self.url='https://atcoder.jp/contests/abc483/tasks/abc483_a?lang=en'
    def tearDown(self):self.temp.cleanup()
    def client(self,transport):return PublicClient(Path(self.temp.name),transport=transport,spacing=0)
    def test_temporary_tls_drop_recovers_without_poisoning_the_contest_host(self):
        transport=Mock(side_effect=[URLError(ssl.SSLEOFError('EOF')), (b'published task',None)])
        client=self.client(transport)
        with patch.object(client.stop,'wait',return_value=False):self.assertEqual(client.text(self.url),'published task')
        self.assertEqual(transport.call_count,2);self.assertNotIn('atcoder.jp',client.backoff)
    def test_access_denial_is_not_retried_or_bypassed(self):
        transport=Mock(side_effect=HTTPError(self.url,403,'denied',{},None));client=self.client(transport)
        with self.assertRaises(RuntimeError):client.text(self.url)
        self.assertEqual(transport.call_count,1);self.assertIn('atcoder.jp',client.backoff)
    def test_certificate_errors_are_not_retried(self):
        transport=Mock(side_effect=URLError(ssl.SSLCertVerificationError('invalid certificate')))
        with self.assertRaises(RuntimeError):self.client(transport).text(self.url)
        self.assertEqual(transport.call_count,1)
    def test_retries_are_bounded(self):
        transport=Mock(side_effect=ssl.SSLEOFError('EOF'));client=self.client(transport)
        with patch.object(client.stop,'wait',return_value=False),self.assertRaises(RuntimeError):client.text(self.url)
        self.assertEqual(transport.call_count,3);self.assertIn('atcoder.jp',client.backoff)

def portrait(color):
    def chunk(kind,raw):return struct.pack('!I',len(raw))+kind+raw+struct.pack('!I',zlib.crc32(kind+raw)&0xffffffff)
    raw=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',1,1,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0'+bytes(color)))+chunk(b'IEND',b'')
    data='data:image/png;base64,'+base64.b64encode(raw).decode()
    return {'avatarData':data,'avatarHash':hashlib.sha256(data.encode()).hexdigest()}

class Training:
    def __init__(self):
        self.lock=threading.RLock();self.closed=False;self.admin_mode=False
        self.profile={'endpoint':'https://47.82.84.74','user_id':'11111111-1111-4111-8111-111111111111','auth_token':'isolated-token'}
    def _ranking_profile(self):return dict(self.profile)
    def _now(self):return dt.datetime.now(dt.timezone.utc)

class ProfileRefreshTests(unittest.TestCase):
    def setUp(self):self.training=Training();self.client=LeaderboardClient(self.training)
    def tearDown(self):self.client.closed=True
    def test_changed_avatar_retires_old_hash_and_reuses_verified_new_bytes(self):
        first,second=portrait((255,0,0,255)),portrait((0,0,255,255));target='22222222-2222-4222-8222-222222222222'
        self.client._request=Mock(side_effect=[first,second])
        with patch('leaderboard.time.monotonic',return_value=100):self.assertEqual(self.client.avatar(target,first['avatarHash']),first)
        with patch('leaderboard.time.monotonic',return_value=110):self.assertEqual(self.client.avatar(target,first['avatarHash']),first)
        self.assertEqual(self.client._request.call_count,1)
        with patch('leaderboard.time.monotonic',return_value=116):
            self.assertEqual(self.client.avatar(target,first['avatarHash']),second)
            self.assertEqual(self.client.avatar(target,second['avatarHash']),second)
        self.assertEqual(self.client._request.call_count,2)
        self.assertTrue(all(key[-1]==second['avatarHash'] for key in self.client.avatar_cache))
    def test_visible_board_updates_profile_metadata_without_full_sync_or_image_downloads(self):
        entered,release=threading.Event(),threading.Event()
        date=self.training._now().astimezone(dt.timezone(dt.timedelta(hours=8))).date().isoformat()
        old={'period':'daily','date':date,'entries':[{'avatarHash':'old'}]}
        new={'period':'daily','date':date,'entries':[{'avatarHash':'new'}]}
        self.client.cache['daily']=(time.monotonic()-25,old,date)
        self.client.snapshot=Mock(return_value={'configured':True,'status':'ready'})
        self.client.queue_sync=Mock()
        def request(*args):entered.set();release.wait(2);return new
        self.client._request=Mock(side_effect=request)
        try:
            before=time.monotonic();value=self.client.rankings('daily')
            self.assertLess(time.monotonic()-before,.5);self.assertEqual(value['entries'],old['entries']);self.assertTrue(entered.wait(1))
        finally:release.set()
        deadline=time.monotonic()+2
        while self.client.board_refreshing and time.monotonic()<deadline:time.sleep(.01)
        self.assertEqual(self.client.rankings('daily')['entries'],new['entries'])
        self.client.queue_sync.assert_not_called()
        self.assertEqual(self.client._request.call_args.args[1:3],('GET','/v1/leaderboard?period=daily'))

class PresentationTests(unittest.TestCase):
    def test_focus_uses_the_verified_browser_pid_and_restores_the_page_title(self):
        browser=BrowserProcess(Path(tempfile.gettempdir())/'tb-166-presentation-unused')
        browser.request=Mock(return_value={'webSocketDebuggerUrl':'ws://127.0.0.1:1/devtools/browser/fixture'})
        inspector=Mock();inspector.call.side_effect=[{'windowId':3,'bounds':{'windowState':'normal'}},{'processInfo':[{'type':'browser','id':123}]}]
        page=Mock();page.evaluate.return_value='Original page title'
        with patch('external_browser.DevToolsPage',return_value=inspector),patch('browser_presentation.present_window',return_value=True) as present:
            self.assertTrue(browser.present_page('target',page,True))
        self.assertEqual(present.call_args.args[0],123);self.assertTrue(present.call_args.args[1].startswith('[ToBe-'));self.assertTrue(present.call_args.args[2])
        page.call.assert_called_once_with('Page.bringToFront');self.assertIn('Original page title',page.evaluate.call_args.args[0])
    def test_opening_a_pending_attempt_does_not_replay_it_and_hides_internal_visibility_flag(self):
        bridge=ExternalBrowserBridge(Path(tempfile.gettempdir())/'tb-166-state-unused')
        url='https://atcoder.jp/contests/abc483/tasks/abc483_a'
        bridge.sessions['fixture']={'sessionId':'fixture','originalUrl':url,'code':'int main(){}','language':'cpp17','status':'judging','attempted':True,'intent':False,'explicitVisible':False}
        try:
            bridge.open(url,'int main(){}','Fixture')
            self.assertTrue(bridge.sessions['fixture']['explicitVisible']);self.assertFalse(bridge.sessions['fixture']['intent'])
            self.assertNotIn('explicitVisible',bridge.status('fixture'))
        finally:bridge.on_closing()

if __name__=='__main__':unittest.main()
