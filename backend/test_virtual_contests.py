"""Original-site VP start receipts; no registration or official submission."""
import datetime as dt
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
import test_training as fixtures
from training import ServiceError,iso
from virtual_contests import virtual_spec,confirmed_receipt,start_replay

class VirtualSpecTests(unittest.TestCase):
    def test_only_a_common_exact_contest_can_start_original_vp(self):
        rows=[{'url':'https://codeforces.com/contest/2278/problem/'+letter} for letter in 'ABC']
        spec=virtual_spec(rows,135)
        self.assertEqual(spec['registrationUrl'],'https://codeforces.com/contestRegistration/2278/virtual/true')
        self.assertTrue(spec['required'])
        self.assertIsNone(virtual_spec([*rows,{'url':'https://codeforces.com/contest/2277/problem/A'}],135))
        self.assertIsNone(virtual_spec([{'url':'https://atcoder.jp/contests/abc480/tasks/abc480_a'}],100))
        self.assertIsNone(virtual_spec([{'url':'https://evil.invalid/contest/2278/problem/A'}],100))
        self.assertEqual(virtual_spec([{'url':'https://qoj.ac/problem/1','contestId':'3767'}],300)['platform'],'QOJ')

    def test_forged_or_incomplete_receipts_are_not_clock_authority(self):
        spec=virtual_spec([{'url':'https://codeforces.com/gym/106534/problem/A'}],300)
        now=dt.datetime(2026,11,4,tzinfo=dt.timezone.utc)
        receipt={**spec,'confirmed':True,'startedAt':iso(now),'deadline':iso(now+dt.timedelta(minutes=300))}
        self.assertEqual(confirmed_receipt(spec,receipt,now)['startedAt'],receipt['startedAt'])
        for change in [{'confirmed':False},{'contestId':'another'},{'url':'https://evil.invalid'},{'deadline':iso(now+dt.timedelta(minutes=2))},{'startedAt':iso(now+dt.timedelta(minutes=10))}]:
            with self.assertRaises(ServiceError):confirmed_receipt(spec,{**receipt,**change},now)

class VirtualReplayTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown
    def prepare(self):
        for index,row in enumerate(self.library.rows):row['url']='https://codeforces.com/contest/2278/problem/'+chr(65+index)
        plan=self.service.preview_contest({'count':3,'duration':120,'min':1000,'max':2100})['plan']
        plan['constraints']['strategy']='replay'
        return {'previewId':plan['previewId'],'ids':[slot['id'] for slot in plan['slots']],'duration':120}

    def test_original_start_failure_leaves_the_local_preview_and_clock_unstarted(self):
        body=self.prepare();start=Mock(side_effect=ServiceError(409,'Original registration not confirmed'))
        server=SimpleNamespace(work_start_lock=threading.RLock(),original_virtual_starter=start)
        with self.assertRaises(ServiceError):start_replay(server,self.service,body)
        self.assertIsNone(self.service.active_contest())
        self.assertIn(tuple(body['ids']),self.service.previews)
        self.assertEqual(start.call_count,1)

    def test_both_clocks_use_the_provider_confirmed_future_start(self):
        body=self.prepare();began=self.clock()+dt.timedelta(seconds=30)
        def start(spec,training):return {**spec,'confirmed':True,'startedAt':iso(began),'deadline':iso(began+dt.timedelta(minutes=120))}
        result=start_replay(SimpleNamespace(work_start_lock=threading.RLock(),original_virtual_starter=start),self.service,body)
        contest=result['contest'];self.assertEqual(contest['startedAt'],iso(began));self.assertEqual(contest['deadline'],iso(began+dt.timedelta(minutes=120)))
        self.assertTrue(contest['constraints']['originalVirtual']['confirmed'])
        with self.assertRaisesRegex(ServiceError,'尚未开始'):self.service.assert_official_allowed(body['ids'][0],contest['id'])
        self.clock.advance(seconds=31)
        self.assertIsNotNone(self.service.assert_official_allowed(body['ids'][0],contest['id']))

    def test_an_old_desktop_cannot_silently_start_local_cf_clock_without_vp(self):
        body=self.prepare()
        with self.assertRaises(ServiceError):start_replay(SimpleNamespace(work_start_lock=threading.RLock()),self.service,body)
        self.assertIsNone(self.service.active_contest())
