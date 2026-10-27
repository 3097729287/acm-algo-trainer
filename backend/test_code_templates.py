"""Account isolation, optimistic edits, deletion and private snapshot round trips."""
import copy,json,unittest
import test_training as fixtures
from code_templates import builtins,catalog,save
from account_sync import merge_states
from training import ServiceError

class TemplateTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown

    def create(self):
        return save(self.service,{'title':'最短路笔记','category':'图论','language':'cpp17','code':'// user code\nint answer = 42;','notes':'自建内容'})['template']

    def test_builtins_are_self_contained_and_cannot_be_overwritten(self):
        values=builtins();self.assertGreaterEqual(len(values),24)
        self.assertEqual(len({item['id'] for item in values}),len(values))
        for item in values:
            self.assertTrue(item['notes'] and item['example'] and item['code'])
            with self.assertRaises(ServiceError):save(self.service,dict(id=item['id'],title='overwrite',code='x',language='cpp17'))
        self.assertEqual(len(catalog(self.service)['templates']),len(values))

    def test_custom_code_survives_reload_and_stale_write_cannot_erase_it(self):
        item=self.create();first=copy.deepcopy(item)
        second=save(self.service,{'id':item['id'],'revision':item['revision'],'title':'保留我的代码','category':'图论','language':'cpp17','code':item['code']+'\n// changed'})['template']
        self.assertNotEqual(first['revision'],second['revision'])
        with self.assertRaises(ServiceError) as issue:save(self.service,{**first,'builtin':False})
        self.assertEqual(issue.exception.status,400)
        with self.assertRaises(ServiceError) as issue:save(self.service,{key:first[key] for key in ['id','revision','title','category','language','code']})
        self.assertEqual(issue.exception.status,409)
        own=[item for item in catalog(self.service)['templates'] if not item['builtin']]
        self.assertEqual(len(own),1);self.assertEqual(own[0]['code'],second['code'])

    def test_delete_keeps_private_tombstone_and_other_template(self):
        first=self.create();second=self.create()
        save(self.service,dict(id=first['id'],revision=first['revision'],delete=True))
        self.assertEqual([item['id'] for item in catalog(self.service)['templates'] if not item['builtin']],[second['id']])
        stored=json.loads(self.service.connection.execute('SELECT value FROM account_preferences WHERE key=?',(first['id'],)).fetchone()[0])
        self.assertTrue(stored['deleted']);self.assertEqual(stored['code'],first['code'])

    def test_templates_use_existing_private_sync_and_keep_conflicting_source(self):
        item=self.create();row=dict(self.service.connection.execute('SELECT * FROM account_preferences WHERE key=?',(item['id'],)).fetchone())
        local={'format':'tb-account-state-v1','tables':{'account_preferences':[row]},'publicAccounts':{}}
        from account_sync import TABLES
        for table in TABLES:local['tables'].setdefault(table,[])
        remote=copy.deepcopy(local);data=json.loads(remote['tables']['account_preferences'][0]['value']);data['code']='// other device';remote['tables']['account_preferences'][0]['value']=json.dumps(data)
        merged=merge_states(remote,local)
        self.assertEqual(len(merged['tables']['account_preferences']),1)
        self.assertEqual(len(merged['tables']['account_sync_conflicts']),1)
        self.assertIn('// other device',json.dumps(merged))
        self.assertIn('// user code',json.dumps(merged))

    def test_code_limits_and_language_are_checked_before_writing(self):
        for code,language in [('x'*(65536+1),'cpp17'),('x','javascript'),('','cpp17')]:
            with self.assertRaises(ServiceError):save(self.service,dict(title='test',language=language,code=code))
        self.assertFalse([item for item in catalog(self.service)['templates'] if not item['builtin']])

if __name__=='__main__':unittest.main()
