"""Real HTTP sync, interrupted transfer and lazy historical-code restoration."""
import copy,datetime as dt,json,unittest
from unittest.mock import patch
import test_account_sync as fixtures
from training import ServiceError

class ChunkSyncTests(unittest.TestCase):
    setUp=fixtures.CloudStateTests.setUp
    tearDown=fixtures.CloudStateTests.tearDown
    start=fixtures.CloudStateTests.start
    stop=fixtures.CloudStateTests.stop
    call=fixtures.CloudStateTests.call
    signup=fixtures.CloudStateTests.signup
    login=fixtures.CloudStateTests.login
    other_computer=fixtures.CloudStateTests.other_computer
    call_other=fixtures.CloudStateTests.call_other

    def pause(self):
        sync=self.server.accounts.state_sync;sync.close();sync.stop.clear();return sync

    def test_old_code_is_not_downloaded_until_opened_but_original_local_copy_survives(self):
        self.signup();self.assertEqual(self.login()[0],200)
        sync=self.pause();service=self.server.training
        code='// exact historical unicode 旧代码\nint main(){return 0;}\n'
        result=service.record_official({'id':'fixture::A','url':'https://codeforces.com/contest/1/problem/A','code':code},
            {'status':'finished','submissionId':'123456789','verdict':'AC'})
        identity=result['id']
        with service.lock:service.connection.execute("UPDATE submissions SET submitted_at='2025-01-02T00:00:00Z',finished_at='2025-01-02T00:00:01Z' WHERE id=?",(identity,))
        sync.flush()
        self.assertTrue(sync.chunks.enabled)
        self.assertEqual(service.connection.execute('SELECT code FROM submissions WHERE id=?',(identity,)).fetchone()[0],code)
        other=self.other_computer();status,answer=self.call_other(other,'/api/account/login',{'loginId':'account_a','password':'fixture-password'})
        self.assertEqual(status,200,answer)
        self.assertEqual(other.training.connection.execute('SELECT code FROM submissions WHERE id=?',(identity,)).fetchone()[0],'')
        ref=other.training.connection.execute('SELECT reference FROM account_sync_code_refs WHERE submission_id=?',(identity,)).fetchone()
        self.assertIsNotNone(ref)
        self.assertEqual(other.training.submission(identity)['submission']['code'],code)
        # Re-opening uses the durable SQLite cache, including when offline.
        with patch.object(other.accounts.state_sync.chunks,'request',side_effect=AssertionError('code fetched twice')):
            self.assertEqual(other.training.submission(identity)['submission']['code'],code)

    def test_one_draft_edit_uploads_only_changed_chunks_and_a_failed_commit_resumes(self):
        self.signup();self.assertEqual(self.login()[0],200)
        sync=self.pause();self.server.training.save_draft('fixture::A','first saved draft');sync.flush()
        root_before=sync.chunks.request('GET','/v2/accounts/state')['root']
        calls=[];original=sync.chunks.request
        def request(method,path,body=None,**kwargs):
            calls.append((method,path,len(json.dumps(body)) if body else 0))
            return original(method,path,body,**kwargs)
        self.server.training.save_draft('fixture::A','second saved draft')
        with patch.object(sync.chunks,'request',side_effect=request):sync.flush()
        uploads=[c for c in calls if c[0]=='POST' and c[1]=='/v2/accounts/state/objects']
        # Saving also updates the existing language preference and training
        # journal. All such actual writes may form small changed buckets.
        self.assertLessEqual(len(uploads),20,'a small edit must not upload the entire journal')
        self.assertTrue(uploads)
        self.assertLess(sum(c[2] for c in uploads),8192)
        self.assertNotEqual(sync.chunks.request('GET','/v2/accounts/state')['root'],root_before)
        self.server.training.save_draft('fixture::A','third survives interruption')
        before=sync.revision
        def fail(method,path,body=None,**kwargs):
            if method=='PUT' and path=='/v2/accounts/state':raise ServiceError(503,'fixture interrupted before commit')
            return original(method,path,body,**kwargs)
        with patch.object(sync.chunks,'request',side_effect=fail),self.assertRaises(ServiceError):sync.flush()
        self.assertEqual(sync.revision,before)
        self.assertEqual(original('GET','/v2/accounts/state')['revision'],before)
        calls.clear()
        with patch.object(sync.chunks,'request',side_effect=request):sync.flush()
        self.assertFalse([c for c in calls if c[0]=='POST' and c[1]=='/v2/accounts/state/objects'],'confirmed uploaded chunks should resume without retransmission')
        self.assertEqual(sync.revision,before+1)
        self.assertEqual(self.server.training.problem('fixture::A')['draft'],'third survives interruption')

    def test_corrupted_cloud_objects_do_not_replace_local_learning_state(self):
        self.signup();self.assertEqual(self.login()[0],200)
        sync=self.pause();self.server.training.save_draft('fixture::A','still safe');sync.flush()
        state,_=sync._capture();root=sync.chunks.pack(state)
        # A fresh machine cannot trust a server-supplied chunk merely because
        # its URL resembles a checksum. Validate compressed bytes and size.
        from account_chunks import ChunkTransport
        original=sync.chunks._cached
        with patch.object(sync.chunks,'_cached',return_value=None),patch.object(sync.chunks,'request',return_value={'kind':'data','data':'YWJj','children':[]}):
            with self.assertRaises(ValueError):sync.chunks.read_blob(root)
        self.assertEqual(self.server.training.problem('fixture::A')['draft'],'still safe')

    def test_recovery_only_code_remains_reachable_and_cached_corruption_is_rejected(self):
        self.signup();self.assertEqual(self.login()[0],200)
        sync=self.pause()
        from account_chunks import CODE_PREFIX,encode
        root=sync.chunks.write_blob(b'preserved conflicting source')
        reference=CODE_PREFIX+encode({'root':root,'sha256':'a'*64,'bytes':28}).decode('utf8')
        state,_=sync._capture()
        state['tables']['submissions']=[]
        state['tables']['account_sync_conflicts']=[{'id':'recovery','data':json.dumps({'table':'submissions','row':{'id':'old','code':reference}})}]
        packed=sync.chunks.pack(state);reachable=set();todo=[packed]
        while todo:
            key=todo.pop()
            if key in reachable:continue
            reachable.add(key);todo.extend(json.loads(sync.chunks._cached(key)['children']))
        self.assertIn(root,reachable,'GC must retain code referenced only by conflict recovery')
        sync.service.connection.execute('UPDATE account_sync_objects SET payload=? WHERE hash=?',(b'corrupt',packed))
        with self.assertRaises(ValueError):sync.chunks.read_blob(packed)

    def test_migrated_account_never_silently_restores_an_older_v1_snapshot(self):
        self.signup();self.assertEqual(self.login()[0],200)
        sync=self.pause();self.assertEqual(sync.meta['transport'],2)
        with patch.object(sync.chunks,'request',return_value={'protocol':2,'revision':0,'legacy':True}):
            with self.assertRaises(ServiceError) as rejected:sync.chunks.negotiate()
        self.assertEqual(rejected.exception.status,503)

    def test_initial_negotiation_waits_for_rate_limit_but_other_login_errors_fail_fast(self):
        self.signup();self.assertEqual(self.login()[0],200)
        sync=self.pause();answer={'protocol':2,'revision':sync.revision,'unchanged':True}
        with patch.object(sync.accounts,'_remote',side_effect=[*[ServiceError(429,'fixture rate limit') for _ in range(12)],answer]) as remote,patch.object(sync.stop,'wait',return_value=False):
            sync.chunks.negotiate()
        self.assertEqual(remote.call_count,13)
        self.assertEqual(self.server.accounts.session['userId'],sync.owner)
        with patch.object(sync.accounts,'_remote',side_effect=ServiceError(503,'fixture unavailable')) as remote:
            with self.assertRaises(ServiceError):sync.chunks.negotiate()
        self.assertEqual(remote.call_count,1)

    def test_many_old_source_files_share_bounded_archives_without_changing_bytes(self):
        self.signup();self.assertEqual(self.login()[0],200)
        sync=self.pause();state,_=sync._capture();original={}
        for i in range(1200):
            identity=f'archive-{i:05d}'
            code=f'// source {i} 中文\n'+('int x = 42;\n'*40)
            original[identity]=code
            state['tables']['submissions'].append({'id':identity,'code':code,'submitted_at':'2025-01-02T00:00:00Z','finished_at':'2025-01-02T00:00:01Z'})
        value=sync.chunks.canonicalize(state)
        from account_chunks import code_reference
        roots=set()
        for row in value['tables']['submissions']:
            ref=code_reference(row['code']);roots.add(ref['root'])
            raw=sync.chunks.read_blob(ref['root'],262144)
            self.assertEqual(raw[ref['offset']:ref['offset']+ref['bytes']].decode('utf8'),original[row['id']])
        self.assertLessEqual(len(roots),32,'small historical code should not require one HTTP object per submission')
        self.assertEqual(sync.chunks.canonicalize(state),value,'archives must stay stable after the initial packing')

if __name__=='__main__':unittest.main()
