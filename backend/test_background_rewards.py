import datetime as dt
import json
import unittest
import uuid
from unittest.mock import patch
import test_training as fixtures
from training import TrainingService,ServiceError,iso
from background_rewards import deliver_completed,record_eligible

class BackgroundRewardsTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown

    def replay(self,duration=None):
        body={'contest':'fixture'}
        if duration is not None:body['duration']=duration
        plan=self.service.preview_replay(body)['plan']
        return self.service.start_contest({'ids':[slot['id'] for slot in plan['slots']],'duration':plan['duration']})['contest']

    def ac(self,contest,identity,*,scope='official',verdict='AC',submitted_at=None,finished=True):
        with self.service._write() as db:
            db.execute('INSERT INTO submissions(id,problem_id,contest_id,mode,code,submitted_at,finished_at,scope,verdict) VALUES(?,?,?,?,?,?,?,?,?)',('receipt-'+uuid.uuid4().hex,identity,contest['id'],'submit','',submitted_at or iso(self.clock()),iso(self.clock()) if finished else None,scope,verdict))

    def proof(self,contest):
        record=self.service._contest_record(contest['id'])
        with self.service._write() as db:return record_eligible(self.service,db,record)

    def finish(self,contest,minutes=60):
        self.clock.advance(minutes=minutes)
        return self.service.finish_contest(contest['id'])

    def test_only_new_default_duration_full_original_replays_have_reward_provenance(self):
        contest=self.replay()
        self.assertEqual(contest['constraints']['backgroundReward']['originalDuration'],120)
        self.service.cancel_contest(contest['id'])
        custom=self.replay(60)
        self.assertNotIn('backgroundReward',custom['constraints'])
        self.service.cancel_contest(custom['id'])
        mock=fixtures.ServiceTests.contest(self)
        self.assertNotIn('backgroundReward',mock['constraints'])
        self.assertIsNone(self.proof(mock))

    def test_default_duration_half_time_boundary_and_two_distinct_real_acs(self):
        contest=self.replay();self.ac(contest,'fixture::A');self.ac(contest,'fixture::B')
        self.finish(contest,59)
        self.assertIsNone(self.proof(contest))
        again=self.replay();self.ac(again,'fixture::A');self.ac(again,'fixture::A');self.ac(again,'fixture::B',scope='samples',verdict='SAMPLE_PASS')
        self.clock.advance(minutes=60)
        self.ac(again,'fixture::C')
        self.service.finish_contest(again['id'])
        value=self.proof(again)
        self.assertEqual(len(value['accepted']),2)
        self.assertEqual(value['finishedAt']-value['startedAt'],3600000)

    def test_cancelled_and_historical_unproven_records_are_never_rewarded(self):
        contest=self.replay();self.ac(contest,'fixture::A');self.ac(contest,'fixture::B');self.clock.advance(minutes=90)
        self.service.cancel_contest(contest['id']);self.assertIsNone(self.proof(contest))
        old=self.replay();self.ac(old,'fixture::A');self.ac(old,'fixture::B');self.finish(old)
        with self.service._write() as db:
            config=json.loads(db.execute('SELECT config FROM contests WHERE id=?',(old['id'],)).fetchone()[0]);config.pop('backgroundReward')
            db.execute('UPDATE contests SET config=? WHERE id=?',(json.dumps(config),old['id']))
            db.execute("DELETE FROM account_preferences WHERE key LIKE 'background-%'")
        with patch('gameplay._request') as relay:
            self.assertIsNone(deliver_completed(self.service));relay.assert_not_called()

    def test_late_judging_counts_only_submissions_made_inside_the_finished_replay(self):
        contest=self.replay();self.ac(contest,'fixture::A');self.clock.advance(minutes=60)
        in_window=iso(self.clock());self.service.finish_contest(contest['id']);self.assertIsNone(self.proof(contest))
        self.clock.advance(minutes=1);self.ac(contest,'fixture::B');self.assertIsNone(self.proof(contest))
        self.ac(contest,'fixture::C',submitted_at=in_window)
        self.assertEqual(len(self.proof(contest)['accepted']),2)

    def test_receipt_outbox_survives_restart_and_lost_replies_with_a_stable_request_id(self):
        contest=self.replay();self.ac(contest,'fixture::A');self.ac(contest,'fixture::B');self.finish(contest)
        with patch('gameplay._request',side_effect=ServiceError(503,'isolated response loss')) as relay:
            with self.assertRaises(ServiceError):deliver_completed(self.service,contest['id'])
            first=relay.call_args.args[3]
        self.service.close();self.service=TrainingService(self.library,self.db,self.assets,self.judge,self.clock,self.root/'backups')
        owner=self.service._ranking_profile()['user_id']
        with patch('gameplay._request',return_value={'owner':owner,'backgroundReward':{'unitId':'isolated-card'},'inventory':{'owner':owner,'units':[]}}) as relay:
            self.assertEqual(deliver_completed(self.service)['backgroundReward']['unitId'],'isolated-card')
            self.assertEqual(relay.call_args.args[3],first)
            self.assertIsNone(deliver_completed(self.service));self.assertEqual(relay.call_count,1)

    def test_account_switch_does_not_deliver_another_owners_replay_proof(self):
        contest=self.replay();self.ac(contest,'fixture::A');self.ac(contest,'fixture::B');self.finish(contest)
        with patch.object(self.service,'_ranking_profile',return_value={'user_id':'other-owner'}),patch('gameplay._request') as relay:
            # The pending record was created for the original account. A restore
            # into another account must not turn it into that account's reward.
            self.assertIsNone(deliver_completed(self.service));relay.assert_not_called()

if __name__=='__main__':unittest.main()
