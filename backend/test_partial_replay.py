"""Partial original contests retain their real slots without blocking ready tasks."""
import unittest
from unittest.mock import patch
import test_training as fixtures
from training import ServiceError


class PartialReplayTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown

    def prepare(self):
        self.library.rows=self.library.rows[:3]
        for row,letter in zip(self.library.rows,['A1','A2','C']):
            row.update(contest='partial',problem=letter,contestProblemCount=4,catalogContentReady=letter!='A1',catalogReplayReady=letter!='A1')
        self.library.rows[0].update(catalogHidden=True,statementRetired=True,statementRetirementPolicy='public-statement-audit-v1',statementPriorVisibility={})
        self.ready=patch.object(self.assets,'candidates',side_effect=lambda rows:[dict(row,judgeScope='official') for row in rows if row['catalogReplayReady']])
        self.ready.start();self.addCleanup(self.ready.stop)

    def test_incomplete_roster_starts_preserves_letters_and_blocks_only_missing_slot(self):
        self.prepare()
        event=self.service.replay_events()['events'][0]
        self.assertFalse(event['complete']);self.assertEqual((event['count'],event['expectedCount']),(3,4))
        with patch.object(self.assets,'problem',side_effect=AssertionError('Preview must not fetch missing statements')):
            plan=self.service.preview_replay({'contest':'partial'})['plan']
        self.assertEqual([slot['letter'] for slot in plan['slots']],['A1','A2','C'])
        self.assertEqual([slot['statementAvailable'] for slot in plan['slots']],[False,True,True])
        contest=self.service.start_contest({'ids':[slot['id'] for slot in plan['slots']],'previewId':plan['previewId'],'duration':plan['duration']})['contest']
        self.assertEqual(len(contest['slots']),3)
        self.assertEqual(self.service.workspace()['training'],[])
        self.assertTrue(self.service.problem('fixture::B',contest['id'])['statementAvailable'])
        for operation in [lambda:self.service.problem('fixture::A',contest['id']),lambda:self.service.save_draft('fixture::A','code',contest['id']),lambda:self.service.assert_official_allowed('fixture::A',contest['id'])]:
            with self.assertRaisesRegex(ServiceError,'题面缺失'):operation()
        self.service.finish_contest(contest['id'])
        self.assertEqual(self.service.workspace()['training'],[])

    def test_ready_set_is_rechecked_at_start_without_requiring_the_whole_roster(self):
        self.prepare();plan=self.service.preview_replay({'contest':'partial'})['plan']
        self.library.rows[1]['catalogReplayReady']=False
        contest=self.service.start_contest({'ids':[slot['id'] for slot in plan['slots']],'duration':plan['duration']})['contest']
        self.assertEqual([slot['statementAvailable'] for slot in contest['slots']],[False,False,True])

    def test_zero_readable_problems_still_returns_a_specific_error(self):
        self.prepare()
        for row in self.library.rows:row['catalogReplayReady']=False
        with self.assertRaisesRegex(ServiceError,'暂无可打开'):self.service.preview_replay({'contest':'partial'})

if __name__=='__main__':unittest.main()
