"""Starting programs persist privately and never replace saved work on open."""
import copy
import json
import unittest

import test_training as fixtures
from initial_code import DEFAULTS, catalog, choose, save, selected
from training import ServiceError, TrainingService
from account_sync import merge_states


class InitialCodeTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown

    def create(self,language='cpp17',code='// my starter\nint main() {}\n'):
        return save(self.service,{'title':'Contest starter','language':language,'code':code})['template']

    def choose(self,item):
        value=catalog(self.service)
        return choose(self.service,{'id':item['id'],'language':item['language'],'revision':value['revisions'][item['language']]})

    def test_default_matches_existing_starter_and_reading_does_not_write(self):
        before=self.service.connection.total_changes
        value=catalog(self.service)
        self.assertEqual(value['selection'],{'cpp17':'default','python3':'default'})
        self.assertTrue(all(item['title']=='默认' and item['code']==DEFAULTS[item['language']] for item in value['templates']))
        self.assertEqual(self.service.connection.total_changes,before)

    def test_create_choose_reopen_and_language_isolation(self):
        item=self.create();self.choose(item)
        python=self.create('python3','print(input())\n');self.choose(python)
        self.service.close()
        self.service=TrainingService(self.library,self.db,self.assets,self.judge,self.clock,self.root/'backups')
        value=selected(self.service)
        self.assertEqual(value['selection'],{'cpp17':item['id'],'python3':python['id']})
        self.assertEqual({row['language']:row['code'] for row in value['templates']},{'cpp17':item['code'],'python3':python['code']})

    def test_selecting_changes_only_new_program_seed_and_preserves_empty_saved_drafts(self):
        self.service.save_draft('fixture::A','my actual code')
        self.service.save_draft('fixture::B','')
        item=self.create();self.choose(item)
        first=self.service.problem('fixture::A')
        blank=self.service.problem('fixture::B')
        self.assertEqual(first['draft'],'my actual code')
        self.assertEqual(blank['draft'],'')
        self.assertIsNotNone(blank['draftSavedAt'])
        self.assertEqual(first['initialCode']['selection']['cpp17'],item['id'])
        self.assertEqual(self.service.problem('fixture::C')['draft'],'')

    def test_cas_edit_and_selection_reject_stale_writes(self):
        item=self.create();self.choose(item)
        updated=save(self.service,{**{key:item[key] for key in ('id','title','language','revision')},'code':'// updated'})['template']
        with self.assertRaises(ServiceError) as issue:save(self.service,{**{key:item[key] for key in ('id','title','language','revision')},'code':'// stale'})
        self.assertEqual(issue.exception.status,409)
        with self.assertRaises(ServiceError):choose(self.service,{'id':'default','language':'cpp17','revision':''})
        self.assertEqual(selected(self.service)['templates'][0]['code'],updated['code'])

    def test_deletion_tombstone_and_invalid_cross_language_selection(self):
        item=self.create();self.choose(item)
        with self.assertRaises(ServiceError):choose(self.service,{'id':item['id'],'language':'python3','revision':''})
        value=save(self.service,{'id':item['id'],'revision':item['revision'],'delete':True})
        self.assertTrue(value['template']['deleted'])
        self.assertEqual(value['selection']['cpp17'],'default')
        self.assertFalse(any(row['id']==item['id'] for row in value['templates']))
        with self.assertRaises(ServiceError):self.choose(item)

    def test_byte_limits_and_immutable_default(self):
        for body in ({'title':'x','language':'cpp17','code':'中'*22000}, {'title':'x','language':'cpp17','code':'\x00'},
                     {'id':'default','title':'x','language':'cpp17','code':'x'}, {'title':'x','language':'javascript','code':'x'}):
            with self.assertRaises(ServiceError):save(self.service,body)
        self.assertEqual(len(catalog(self.service)['templates']),2)

    def test_private_journal_merge_retains_independent_templates_and_selection(self):
        item=self.create();self.choose(item)
        rows=[dict(row) for row in self.service.connection.execute("SELECT * FROM account_preferences WHERE key LIKE 'initial-code%'")]
        state={'tables':{'account_preferences':rows},'publicAccounts':{}}
        remote=copy.deepcopy(state)
        remote['tables']['account_preferences'].append({'key':'initial-code:'+'a'*32,'value':json.dumps({**item,'id':'initial-code:'+'a'*32,'title':'Other device'}),'updated_at':rows[0]['updated_at']})
        merged=merge_states(remote,state)
        self.assertEqual(len(merged['tables']['account_preferences']),3)


if __name__=='__main__':unittest.main()
