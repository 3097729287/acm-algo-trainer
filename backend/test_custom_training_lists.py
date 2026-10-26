import json
import unittest
from custom_training_lists import read_lists, save_list, PREFIX
from training import TrainingService, ServiceError
from training_list_tags import save_tags
import test_training as fixtures

class CustomTrainingListsTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown

    def test_order_edit_tags_persistence_and_tombstone(self):
        saved=save_list(self.service,{'title':'复习','problemIds':['fixture::B','fixture::A','fixture::B']})['list']
        self.assertEqual([item['problemId'] for item in saved['problems']],['fixture::B','fixture::A'])
        save_tags(self.service,{'listId':saved['id'],'tags':['周末']},{saved['id']})
        changed=save_list(self.service,{'id':saved['id'],'title':'周末复习','problemIds':['fixture::A','fixture::B']})
        self.service.close()
        self.service=TrainingService(self.library,self.db,self.assets,self.judge,self.clock,self.root/'backups')
        self.assertEqual(read_lists(self.service),changed['customLists'])
        save_list(self.service,{'id':saved['id'],'deleted':True})
        self.assertEqual(read_lists(self.service),[])
        raw=self.service.connection.execute('SELECT value FROM account_preferences WHERE key=?',(PREFIX+saved['id'],)).fetchone()[0]
        self.assertTrue(json.loads(raw)['deleted'])

    def test_validation_is_atomic_and_account_owned(self):
        saved=save_list(self.service,{'title':'我的题单','problemIds':['fixture::A']})['list']
        for body in ({'title':''},{'title':42},{'title':'bad\nname'}, {'title':'x','problemIds':['missing']},
                     {'id':saved['id'],'title':None,'deleted':True}, {'id':'custom:00000000-0000-0000-0000-000000000000','title':'x'},
                     {'title':'x','problemIds':['fixture::A']*1001},{'title':'x','owner':'another'}):
            with self.subTest(body=body),self.assertRaises(ServiceError):save_list(self.service,body)
        self.assertEqual(read_lists(self.service),[saved])
        other=TrainingService(self.library,self.root/'other.sqlite3',self.assets,self.judge,self.clock,self.root/'other-backups')
        try:
            self.assertEqual(read_lists(other),[])
            with self.assertRaises(ServiceError):save_list(other,{'id':saved['id'],'title':'changed'})
        finally:other.close()
