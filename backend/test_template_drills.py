"""Exact allowlist, non-unique answer checkers and real in-app template judging."""
import json,os,sys,tempfile,time,unittest
from pathlib import Path
import backend
from library import LibraryDatabase
from template_drills import definitions,generate,bundle,check,is_drill

class DrillTests(unittest.TestCase):
    def test_every_authored_sample_and_full_reference_set_is_valid(self):
        self.assertEqual(len(definitions()),48)
        for identity,item in definitions().items():
            for case in bundle(identity)['cases']:
                self.assertTrue(check(identity,case['input'],case['output'],case['output']),identity)
            self.assertFalse(is_drill(identity+'-forged'))
        self.assertFalse(is_drill('remote:codeforces:1::A'))

    def test_structural_checkers_accept_alternatives_and_reject_invalid_answers(self):
        self.assertTrue(check('template-drill:topological:1','3 1\n0 2\n','1 0 2','0 1 2'))
        self.assertFalse(check('template-drill:topological:1','3 1\n0 2\n','2 1 0','0 1 2'))
        self.assertTrue(check('template-drill:extended-gcd:1','1\n30 18\n','6 2 -3','6 -1 2'))
        self.assertFalse(check('template-drill:extended-gcd:1','1\n30 18\n','3 2 -3','6 -1 2'))
        self.assertFalse(check('template-drill:lis:1','3\n1 1 2\n','2 0 1','2 0 2'))
        self.assertTrue(check('template-drill:lis:1','3\n1 1 2\n','2 1 2','2 0 2'))
        self.assertFalse(check('template-drill:dijkstra:2','3 1 0\n0 1 2\n1\n2\n','2 2 0 2','-1 0'))

    @unittest.skipUnless(os.name=='nt','Windows Job runner')
    def test_template_submission_passes_full_local_cases_without_official_xp(self):
        root=Path(__file__).resolve().parents[1]
        identity='template-drill:dsu:1'
        raw=next(p for p in json.loads((root/'data/library/problems.json').read_text(encoding='utf8')) if p['id']==identity)
        st=next(p['content'] for p in json.loads((root/'data/library/statements.json').read_text(encoding='utf8')) if p['problem_id']==identity)
        source='''import sys
it=iter(map(int,sys.stdin.read().split()));n=next(it);q=next(it);a=list(range(n))
for _ in range(q):
 t=next(it)
 if t==0:
  u,v=next(it),next(it);old=a[v];new=a[u];a=[new if x==old else x for x in a]
 elif t==1:print(int(a[next(it)]==a[next(it)]))
 elif t==2:print(a.count(a[next(it)]))
 else:print(len(set(a)))
'''
        with tempfile.TemporaryDirectory(prefix='tb-template-drill-') as directory:
            folder=Path(directory);library=LibraryDatabase(folder/'library.sqlite3')
            library.import_records([(raw['raw'],raw['encoded'],None,st)],{}, {})
            server=backend.create_server(port=0,require_account=False,training_file=folder/'personal.sqlite3',library_file=library.path,integration_auto_start=False,backup_dir=folder/'backups')
            try:
                service=server.training;service._judge().python=sys.executable
                self.assertTrue(service.problem(identity)['templatePractice'])
                self.assertEqual(service.problem(identity)['judge']['scope'],'template')
                def submit(code,mode='submit'):
                    value=service.submit(identity,code,mode=mode,language='python3')['submission'];deadline=time.monotonic()+30
                    while time.monotonic()<deadline:
                        value=service.submission(value['id'])['submission']
                        if value['finishedAt']:return value
                        time.sleep(.02)
                    self.fail('local judge did not finish')
                passed=submit(source)
                self.assertEqual((passed['verdict'],passed['scope'],passed['passed'],passed['total']),('AC','template',24,24),passed)
                wrong=submit('print(123)')
                self.assertEqual(wrong['verdict'],'WA',wrong)
                sample=submit(source,'run')
                self.assertEqual(sample['verdict'],'SAMPLE_PASS',sample)
                self.assertEqual(service.connection.execute('SELECT COUNT(*) FROM official_first_xp_awards').fetchone()[0],0)
                self.assertEqual(service.connection.execute("SELECT COUNT(*) FROM submissions WHERE scope='official'").fetchone()[0],0)
            finally:server.server_close()

if __name__=='__main__':unittest.main()
