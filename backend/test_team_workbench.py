"""Native bridge tests use disposable personal state and no actual OJ requests."""
import copy
import hashlib
import json
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import uuid

import test_training as fixtures
from training import ServiceError, iso
from team_workbench import authorized, deliver_receipts, mirror, record_receipt, recover_receipts, write


class TeamWorkbenchTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown

    def room(self):
        owner = self.service._ranking_profile()['user_id']
        now = self.clock().timestamp()*1000
        for row in self.library.rows:
            row['url'] = 'https://codeforces.com/contest/123/problem/'+row['problem']
        self.state = {'owner': owner, 'serverNow': now, 'enabled': True, 'protocol': 1,
            'team': {'id': str(uuid.uuid4())}, 'room': {'id': str(uuid.uuid4()), 'teamId': None,
                'status': 'active', 'startedAt': now-1000, 'deadline': now+299000, 'contestTitle': 'isolated team',
                'problemId': 'fixture::A', 'problems': [{'id':r['id'],'url':r['url'],'letter':r['problem'],
                    'title':r['title'],'available':i != 1} for i,r in enumerate(self.library.rows[:3])],
                'document': {'code':'int main() { return 0; }','language':'cpp17','revision':1,'savedAt':now},
                'lease': {'owner':owner,'token':str(uuid.uuid4()),'until':now+15000}}}
        self.state['room']['teamId'] = self.state['team']['id']
        return mirror(self.service,self.state,self.state['room']['id'],create=True)

    def body(self):
        room=self.state['room']
        return {'requestId':str(uuid.uuid4()),'roomId':room['id'],'leaseToken':room['lease']['token'],
                'id':room['problemId'],'code':room['document']['code'],'language':'cpp17','revision':1}

    def remote(self, training, action='state', body=None):
        state=copy.deepcopy(self.state)
        if action == 'authorize':
            self.assertEqual(body['inputSha256'],hashlib.sha256(state['room']['document']['code'].encode()).hexdigest())
            self.assertEqual(body['leaseToken'],state['room']['lease']['token'])
            state['ack']={'authorization':{'id':body['requestId'],'roomId':body['roomId'],'problemId':body['problemId'],
                'url':self.library.rows[0]['url'],'revision':body['revision'],'language':body['language'],
                'purpose':body['purpose'],'inputSha256':body['inputSha256'],
                'issuedAt':state['serverNow'],'expiresAt':state['serverNow']+15000}}
        return state

    def test_team_mirror_preserves_normal_drafts_and_blocks_generic_write_bypasses(self):
        self.service.save_draft('fixture::A','my old private code')
        before=[tuple(r) for r in self.service.connection.execute('SELECT * FROM drafts')]
        contest=self.room()
        self.assertEqual([tuple(r) for r in self.service.connection.execute('SELECT * FROM drafts')],before)
        self.assertFalse(next(s for s in contest['slots'] if s['letter']=='B')['statementAvailable'])
        self.assertEqual(self.service.connection.execute('SELECT COUNT(*) FROM training').fetchone()[0],1)
        for operation in [lambda:self.service.save_draft('fixture::A','bypass',contest['id']),
                          lambda:self.service.submit('fixture::A','bypass',mode='run',contest_id=contest['id']),
                          lambda:self.service.assert_official_allowed('fixture::A',contest['id']),
                          lambda:self.service.finish_contest(contest['id']),
                          lambda:self.service.cancel_contest(contest['id'])]:
            with self.assertRaises(ServiceError):operation()
        self.assertEqual([tuple(r) for r in self.service.connection.execute('SELECT * FROM drafts')],before)
        with authorized(self.service,contest['id']):self.service.save_draft('fixture::A','shared copy',contest['id'])
        self.assertEqual(self.service.connection.execute("SELECT code FROM drafts WHERE context='' AND problem_id='fixture::A'").fetchone()[0],'my old private code')

    def test_native_intent_is_durable_and_retries_do_not_submit_twice(self):
        self.room();body=self.body();calls=[]
        def opener(url,code,title,language='cpp17'):
            calls.append((url,code,language));return {'sessionId':'native-isolated-session','status':'judging','url':url}
        server=SimpleNamespace(training=self.service,official_submitter=opener,browser_preparation=None,register_official_session=Mock())
        with patch('team_workbench.relay',side_effect=self.remote):
            first=write(server,'official-submit',body)
            duplicate=write(server,'official-submit',body)
        self.assertEqual(first['sessionId'],duplicate['sessionId']);self.assertEqual(len(calls),1)
        key='team-native:'+body['requestId']
        journal=json.loads(self.service.connection.execute('SELECT value FROM account_preferences WHERE key=?',(key,)).fetchone()[0])
        self.assertEqual(journal['phase'],'opened')
        context=server.register_official_session.call_args.args[1]
        receipt={'status':'finished','submissionId':'99118822','verdict':'AC','acceptedAt':iso(self.clock())}
        saved=self.service.record_official(context,receipt)
        record_receipt(self.service,saved,context,receipt)
        journal=json.loads(self.service.connection.execute('SELECT value FROM account_preferences WHERE key=?',(key,)).fetchone()[0])
        self.assertEqual(journal['phase'],'receipt-ready');self.assertEqual(journal['localSubmissionId'],saved['id'])
        self.assertEqual(journal['submissionId'],'99118822')
        # A UI-shaped verdict with no persisted source is not an outbox fact.
        before=journal.copy();record_receipt(self.service,{'id':'made-up'},context,{'verdict':'AC'})
        after=json.loads(self.service.connection.execute('SELECT value FROM account_preferences WHERE key=?',(key,)).fetchone()[0])
        self.assertEqual(before,after)

    def test_ambiguous_browser_start_is_retained_without_a_second_open(self):
        self.room();body=self.body();opener=Mock(side_effect=TimeoutError('isolated start timeout'))
        server=SimpleNamespace(training=self.service,official_submitter=opener,browser_preparation=None)
        with patch('team_workbench.relay',side_effect=self.remote):
            with self.assertRaises(TimeoutError):write(server,'official-submit',body)
            with self.assertRaises(ServiceError) as error:write(server,'official-submit',body)
        self.assertEqual(error.exception.code,'TEAM_SUBMISSION_UNCERTAIN');self.assertEqual(opener.call_count,1)

    def test_local_runs_and_peer_scores_do_not_become_personal_acceptance(self):
        contest=self.room();server=SimpleNamespace(training=self.service)
        with patch('team_workbench.relay',side_effect=self.remote):
            answer=write(server,'run',{**self.body(),'sampleRun':True})
        until=time.monotonic()+3
        while True:
            saved=self.service.submission(answer['submission']['id'])['submission']
            if saved['finishedAt'] or time.monotonic()>until:break
            time.sleep(.01)
        self.assertIsNotNone(saved['finishedAt'])
        self.assertEqual(saved['mode'],'run');self.assertNotEqual(saved['scope'],'official')
        self.state['room'].update(status='finished',finishedAt=self.state['serverNow'])
        final=mirror(self.service,self.state,self.state['room']['id'])
        self.assertEqual(final['accepted'],0)
        self.assertEqual(self.service.connection.execute('SELECT COUNT(*) FROM training WHERE accepted_at IS NOT NULL OR mock_due!=0').fetchone()[0],0)
        self.assertFalse(self.service.connection.execute("SELECT 1 FROM account_preferences WHERE key LIKE 'replay-background:%'").fetchone())

    def test_server_roster_owner_or_clock_cannot_be_replaced_by_local_payload(self):
        self.room()
        for change in [{'owner':'different'}, {'room':{**self.state['room'],'deadline':self.state['room']['deadline']+60000}},
                       {'room':{**self.state['room'],'problems':list(reversed(self.state['room']['problems']))}}]:
            with self.assertRaises(ServiceError):mirror(self.service,{**self.state,**change},self.state['room']['id'])
        with self.assertRaises(ServiceError):
            write(SimpleNamespace(training=self.service),'enter',{'roomId':self.state['room']['id'],'totalScore':99})

    def test_receipt_outbox_survives_restart_and_does_not_send_code_or_ui_verdicts(self):
        self.room();body=self.body()
        def opener(url,code,title,language='cpp17'):
            return {'sessionId':'durable-native-session','status':'judging'}
        server=SimpleNamespace(training=self.service,official_submitter=opener,browser_preparation=None,register_official_session=Mock())
        with patch('team_workbench.relay',side_effect=self.remote),patch('team_workbench._bound_handle',return_value='boundFixtureHandle'):
            write(server,'official-submit',body)
        context=server.register_official_session.call_args.args[1]
        receipt={'status':'finished','submissionId':'99882211','verdict':'AC','acceptedAt':iso(self.clock())}
        saved=self.service.record_official(context,receipt)
        with patch('team_workbench.queue_receipts'):
            record_receipt(self.service,saved,context,receipt)
        self.service.close()
        from training import TrainingService
        self.service=TrainingService(self.library,self.db,self.assets,self.judge,self.clock,self.root/'backups')
        key='team-native:'+body['requestId']
        def stored():return json.loads(self.service.connection.execute('SELECT value FROM account_preferences WHERE key=?',(key,)).fetchone()[0])
        with patch('team_workbench.relay',side_effect=ServiceError(503,'isolated offline')):
            deliver_receipts(self.service)
        self.assertEqual(stored()['phase'],'receipt-ready')
        response={'owner':self.state['owner'],'receipt':{'intentId':body['requestId'],'status':'confirmed','submissionId':'99882211','verdict':'AC','source':'isolated-public-provider'}}
        with patch('team_workbench.relay',return_value=response) as network:
            deliver_receipts(self.service);deliver_receipts(self.service)
        self.assertEqual(network.call_count,1)
        args=network.call_args;self.assertEqual(args.kwargs,{'internal':True})
        self.assertEqual(args.args[1],'native-receipt')
        self.assertEqual(set(args.args[2]),{'requestId','intentId','submissionId','handle'})
        self.assertEqual(args.args[2]['handle'],'boundFixtureHandle')
        self.assertEqual(stored()['phase'],'confirmed')

    def test_native_retry_keeps_its_session_after_the_short_authorization_expires(self):
        self.room();body=self.body();opener=Mock(return_value={'sessionId':'same-native-session','status':'judging'})
        server=SimpleNamespace(training=self.service,official_submitter=opener,browser_preparation=None,register_official_session=Mock())
        with patch('team_workbench.relay',side_effect=self.remote):write(server,'official-submit',body)
        self.clock.advance(minutes=1)
        with patch('team_workbench.relay') as remote:
            self.assertEqual(write(server,'official-submit',body)['sessionId'],'same-native-session')
        remote.assert_not_called();self.assertEqual(opener.call_count,1)

    def test_unsupported_native_language_is_rejected_before_the_durable_start(self):
        self.room();body={**self.body(),'language':'python3'}
        def cpp_only(url,code,title):self.fail('unsupported opener was called')
        server=SimpleNamespace(training=self.service,official_submitter=cpp_only)
        with patch('team_workbench.relay',side_effect=self.remote):
            for _ in range(2):
                with self.assertRaises(ServiceError) as error:write(server,'official-submit',body)
                self.assertEqual(error.exception.code,'TEAM_LANGUAGE_UNSUPPORTED')
        self.assertEqual(self.service.connection.execute("SELECT COUNT(*) FROM account_preferences WHERE key LIKE 'team-native:%'").fetchone()[0],0)

    def test_crash_recovery_needs_a_unique_persisted_receipt_with_exact_source(self):
        contest=self.room();body=self.body()
        server=SimpleNamespace(training=self.service,official_submitter=Mock(side_effect=TimeoutError('isolated lost session')),browser_preparation=None)
        with patch('team_workbench.relay',side_effect=self.remote),patch('team_workbench._bound_handle',return_value='boundFixtureHandle'):
            with self.assertRaises(TimeoutError):write(server,'official-submit',body)
        context={'id':body['id'],'contestId':contest['id'],'code':body['code'],'url':self.library.rows[0]['url']}
        receipt={'status':'finished','submissionId':'99112233','verdict':'AC','acceptedAt':iso(self.clock())}
        saved=self.service.record_official(context,receipt)
        key='team-native:'+body['requestId']
        def stored():return json.loads(self.service.connection.execute('SELECT value FROM account_preferences WHERE key=?',(key,)).fetchone()[0])
        original=stored()
        # Two identical uncertain starts cannot claim the same native receipt.
        other=copy.deepcopy(original);other['authorization']['id']=str(uuid.uuid4())
        other_key='team-native:'+other['authorization']['id']
        with self.service._write() as db:db.execute('INSERT INTO account_preferences(key,value,updated_at) VALUES(?,?,?)',(other_key,json.dumps(other),iso(self.clock())))
        with patch('team_workbench.queue_receipts'):
            recover_receipts(self.service)
        self.assertEqual(stored()['phase'],'starting')
        with self.service._write() as db:db.execute('DELETE FROM account_preferences WHERE key=?',(other_key,))
        self.service.close()
        from training import TrainingService
        self.service=TrainingService(self.library,self.db,self.assets,self.judge,self.clock,self.root/'backups')
        with patch('team_workbench.queue_receipts'):
            recover_receipts(self.service);recover_receipts(self.service)
        self.assertEqual(stored()['phase'],'receipt-ready');self.assertEqual(stored()['localSubmissionId'],saved['id'])
        self.assertEqual(stored()['submissionId'],'99112233');self.assertEqual(server.official_submitter.call_count,1)

    def test_receipt_language_is_bound_for_callback_crash_recovery_and_outbox(self):
        contest=self.room();body=self.body()
        server=SimpleNamespace(training=self.service,official_submitter=Mock(side_effect=TimeoutError('isolated interrupted start')),browser_preparation=None)
        with patch('team_workbench.relay',side_effect=self.remote):
            with self.assertRaises(TimeoutError):write(server,'official-submit',body)
        context={'id':body['id'],'contestId':contest['id'],'code':body['code'],
                 'url':self.library.rows[0]['url'],'language':'python3','teamIntentId':body['requestId']}
        receipt={'status':'finished','submissionId':'99112234','verdict':'CE','acceptedAt':iso(self.clock())}
        saved=self.service.record_official(context,receipt)
        # The ordinary native callback persists this existing per-submission
        # language fact. Matching source text alone must not reassign it to a
        # C++ authorization after an uncertain browser start or restart.
        with self.service._write() as db:self.service._save_language(db,'submission-language:'+saved['id'],'python3')
        key='team-native:'+body['requestId']
        def stored():return json.loads(self.service.connection.execute('SELECT value FROM account_preferences WHERE key=?',(key,)).fetchone()[0])
        original=stored()
        def save(value):
            with self.service._write() as db:db.execute('UPDATE account_preferences SET value=? WHERE key=?',(json.dumps(value),key))
        with patch('team_workbench.queue_receipts'):
            record_receipt(self.service,saved,context,receipt)
            callback_phase=stored()['phase'];save(original)
            recover_receipts(self.service)
            recovery_phase=stored()['phase']
        legacy={**original,'phase':'receipt-ready','localSubmissionId':saved['id'],'submissionId':'99112234','handle':'isolatedHandle'}
        save(legacy)
        with patch('team_workbench.relay') as network:deliver_receipts(self.service)
        self.assertEqual((callback_phase,recovery_phase,network.call_count),('starting','starting',0))
        self.assertEqual(stored()['phase'],'receipt-ready','retain the uncertain legacy journal and private record for review')
        self.assertEqual(self.service._read_language('submission-language:'+saved['id']),'python3')
        self.assertEqual(server.official_submitter.call_count,1)

    def test_python_native_callback_persists_language_before_team_receipt_and_restart(self):
        from backend import LocalServer
        self.room();self.state['room']['document'].update(code='print(123)',language='python3')
        body={**self.body(),'language':'python3'}
        calls=[]
        def opener(url,code,title,language='cpp17'):
            calls.append((url,code,language));return {'sessionId':'isolated-python-native','status':'judging'}
        server=SimpleNamespace(training=self.service,official_submitter=opener,browser_preparation=None,register_official_session=Mock())
        with patch('team_workbench.relay',side_effect=self.remote),patch('team_workbench._bound_handle',return_value='isolatedHandle'):
            write(server,'official-submit',body)
        context={**server.register_official_session.call_args.args[1],'sessionId':'isolated-python-native'}
        native=SimpleNamespace(training=self.service,official_session_lock=threading.Lock(),
            official_sessions={'isolated-python-native':context},official_pending_receipts={})
        receipt={'status':'finished','submissionId':'99112235','verdict':'CE','acceptedAt':iso(self.clock())}
        with patch('team_workbench.queue_receipts'):
            saved=LocalServer.record_official_receipt(native,'isolated-python-native',receipt)
        key='team-native:'+body['requestId']
        def stored():return json.loads(self.service.connection.execute('SELECT value FROM account_preferences WHERE key=?',(key,)).fetchone()[0])
        self.assertEqual(stored()['phase'],'receipt-ready')
        self.assertEqual(self.service._read_language('submission-language:'+saved['id']),'python3')
        self.service.close()
        from training import TrainingService
        self.service=TrainingService(self.library,self.db,self.assets,self.judge,self.clock,self.root/'backups')
        server.training=self.service
        answer={'owner':self.state['owner'],'receipt':{'intentId':body['requestId'],'status':'confirmed',
                'submissionId':'99112235','verdict':'CE','source':'explicit-isolated-provider'}}
        with patch('team_workbench.relay',return_value=answer) as network:
            deliver_receipts(self.service);deliver_receipts(self.service)
        self.assertEqual(network.call_count,1);self.assertEqual(stored()['phase'],'confirmed')
        with patch('team_workbench.relay') as remote:
            self.assertEqual(write(server,'official-submit',body)['sessionId'],'isolated-python-native')
        remote.assert_not_called();self.assertEqual(len(calls),1)
