"""Calendar late joins and compact-history reads in disposable training state."""
import datetime as dt
import json
from unittest.mock import patch
import unittest

import test_training as F
from training import ServiceError,iso
from contest_calendar import ContestCalendar,event

class RevisionTests(unittest.TestCase):
    setUp=F.ServiceTests.setUp
    tearDown=F.ServiceTests.tearDown

    def test_compact_history_omits_code_without_loading_the_whole_catalog(self):
        code='precise code\n'*4000;timestamp=iso(self.clock())
        self.service.connection.execute("INSERT INTO submissions(id,problem_id,mode,code,submitted_at,finished_at,verdict,scope,output,stderr,message) VALUES ('record','fixture::A','submit',?,?,?,'WA','local',?,?,?)",(code,timestamp,timestamp,'out'*10000,'err'*10000,'message'*10000))
        with patch.object(self.service,'_library',side_effect=AssertionError('list must not decode the whole library')),patch.object(self.service,'_row',return_value=self.library.rows[0]):
            value=self.service.submissions(results_only=True,compact=True)['submissions'][0]
        self.assertTrue(value['codePending']);self.assertEqual(value['title'],self.library.rows[0]['title'])
        self.assertFalse({'code','output','stderr','message','caseResults'}&value.keys())
        self.assertEqual(self.service.submission('record')['submission']['code'],code)
        self.assertEqual(self.service.submissions()['submissions'][0]['code'],code)

    def test_calendar_late_join_uses_original_start_and_end(self):
        began=self.clock()-dt.timedelta(minutes=25);ended=began+dt.timedelta(hours=2)
        value={'id':'nowcoder:42','url':'https://ac.nowcoder.com/acm/contest/42','startAt':iso(began),'endAt':iso(ended),'contest':'fixture'}
        result=self.service.start_calendar_contest(value)['contest']
        self.assertEqual(result['startedAt'],iso(began));self.assertEqual(result['deadline'],iso(ended))
        self.assertEqual(result['elapsedSeconds'],1500)
        with self.assertRaises(ServiceError):self.service.start_calendar_contest(value)

    def test_calendar_resolver_rejects_future_ended_partial_and_unknown_events(self):
        import tempfile
        with tempfile.TemporaryDirectory() as root:
            clock=1800000000;calendar=ContestCalendar(root,clock=lambda:clock,offline=True)
            current=event('nowcoder',42,'fixture',clock-600,clock+600,'https://ac.nowcoder.com/acm/contest/42')
            calendar.providers['nowcoder']={'contests':[current]}
            with self.assertRaises(ServiceError):calendar.ongoing(current['id'])
            calendar.imports[current['id']]={'status':'ready','title':'fixture'}
            self.assertEqual(calendar.ongoing(current['id'])['contest'],'fixture')
            for at in (clock-601,clock+600):
                calendar.clock=lambda:at
                with self.assertRaises(ServiceError):calendar.ongoing(current['id'])
            with self.assertRaises(ServiceError):calendar.ongoing('nowcoder:999')
            calendar.close()

    def test_real_partial_or_unverified_rosters_are_hidden_without_removing_tasks(self):
        from contest_rules import event_info
        for row in self.library.rows:row.update(catalogContentReady=True,contestProblemCount=9)
        self.assertFalse(event_info('fixture',self.library.rows)['complete'])
        self.assertEqual(self.service.replay_events()['events'],[])
        self.assertEqual(len(self.library.rows),8)
        for row in self.library.rows:row['contestProblemCount']=8
        self.assertEqual(len(self.service.replay_events()['events']),1)
        self.library.rows[0]['catalogContentReady']=False
        self.assertEqual(self.service.replay_events()['events'],[])

if __name__=='__main__':unittest.main()
