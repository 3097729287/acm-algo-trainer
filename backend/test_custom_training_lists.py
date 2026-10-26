import json
import unittest
from custom_training_lists import read_lists, save_list, add_problems, PREFIX, MAX_PROBLEMS
from unittest.mock import patch
from training import TrainingService, ServiceError
import test_training as fixtures

class CustomTrainingListsTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown

    def test_order_edit_persistence_and_tombstone(self):
        saved=save_list(self.service,{'title':'复习','problemIds':['fixture::B','fixture::A','fixture::B']})['list']
        self.assertEqual([item['problemId'] for item in saved['problems']],['fixture::B','fixture::A'])
        changed=save_list(self.service,{'id':saved['id'],'title':'周末复习','problemIds':['fixture::A','fixture::B']})
        self.service.close()
        self.service=TrainingService(self.library,self.db,self.assets,self.judge,self.clock,self.root/'backups')
        self.assertEqual(read_lists(self.service),changed['customLists'])
        save_list(self.service,{'id':saved['id'],'deleted':True})
        self.assertEqual(read_lists(self.service),[])
        raw=self.service.connection.execute('SELECT value FROM account_preferences WHERE key=?',(PREFIX+saved['id'],)).fetchone()[0]
        self.assertTrue(json.loads(raw)['deleted'])
        self.assertEqual(json.loads(raw)['problems'], changed['list']['problems'])
        with self.assertRaises(ServiceError):
            add_problems(self.service,{'listIds':[saved['id']],'problemIds':['fixture::C']})
        with self.assertRaises(ServiceError):
            save_list(self.service,{'id':saved['id'],'title':'不能复活'})

    def test_validation_is_atomic_and_account_owned(self):
        saved=save_list(self.service,{'title':'我的题单','problemIds':['fixture::A']})['list']
        for body in ({'title':''},{'title':42},{'title':'bad\nname'}, {'title':'x','problemIds':['missing']},
                     {'id':saved['id'],'title':None,'deleted':True}, {'id':'custom:00000000-0000-0000-0000-000000000000','title':'x'},
                     {'title':'x','problemIds':['fixture::A']*(MAX_PROBLEMS+1)},{'title':'x','owner':'another'}):
            with self.subTest(body=body),self.assertRaises(ServiceError):save_list(self.service,body)
        self.assertEqual(read_lists(self.service),[saved])
        other=TrainingService(self.library,self.root/'other.sqlite3',self.assets,self.judge,self.clock,self.root/'other-backups')
        try:
            self.assertEqual(read_lists(other),[])
            with self.assertRaises(ServiceError):save_list(other,{'id':saved['id'],'title':'changed'})
        finally:other.close()

    def test_batch_appends_to_multiple_lists_and_deduplicates_aliases(self):
        first=save_list(self.service,{'title':'一','problemIds':['fixture::B']})['list']
        second=save_list(self.service,{'title':'二'})['list']
        self.library.rows[0]['aliasIds']=['alias-a']
        body={'listIds':[first['id'],second['id'],first['id']],'problemIds':['fixture::A','alias-a','fixture::B','fixture::A']}
        result=add_problems(self.service,body)
        self.assertEqual(result['added'],{first['id']:1,second['id']:2})
        by_id={value['id']:value for value in result['customLists']}
        self.assertEqual([item['problemId'] for item in by_id[first['id']]['problems']],['fixture::B','fixture::A'])
        self.assertEqual([item['problemId'] for item in by_id[second['id']]['problems']],['fixture::A','fixture::B'])
        self.assertEqual(add_problems(self.service,body)['added'],{first['id']:0,second['id']:0})
        add_problems(self.service,{'listIds':[first['id']],'problemIds':['fixture::C']})
        result=add_problems(self.service,{'listIds':[first['id']],'problemIds':['fixture::D']})
        self.assertEqual([item['problemId'] for item in next(x for x in result['customLists'] if x['id']==first['id'])['problems']],['fixture::B','fixture::A','fixture::C','fixture::D'])

    def test_batch_failure_is_atomic_and_does_not_write_other_accounts(self):
        first=save_list(self.service,{'title':'一','problemIds':['fixture::A']})['list']
        second=save_list(self.service,{'title':'二'})['list']
        original=read_lists(self.service)
        for body in [
            {'listIds':[first['id'],'custom:00000000-0000-0000-0000-000000000000'],'problemIds':['fixture::B']},
            {'listIds':[first['id'],second['id']],'problemIds':['fixture::B','missing']},
            {'listIds':[first['id'],'public'],'problemIds':['fixture::B']},
            {'listIds':[],'problemIds':['fixture::B']},
            {'listIds':[first['id']],'problemIds':[]},
            {'listIds':[first['id']],'problemIds':['fixture::B'],'owner':'other'},
        ]:
            with self.subTest(body=body),self.assertRaises(ServiceError):add_problems(self.service,body)
            self.assertEqual(read_lists(self.service),original)
        with patch('custom_training_lists.MAX_PROBLEMS',1),self.assertRaises(ServiceError):
            add_problems(self.service,{'listIds':[second['id'],first['id']],'problemIds':['fixture::B']})
        self.assertEqual(read_lists(self.service),original)
        other=TrainingService(self.library,self.root/'other.sqlite3',self.assets,self.judge,self.clock,self.root/'other-backups')
        try:
            with self.assertRaises(ServiceError):add_problems(other,{'listIds':[first['id']],'problemIds':['fixture::A']})
            self.assertEqual(read_lists(other),[])
        finally:other.close()

    def test_large_filtered_batch_resolves_catalogue_once(self):
        saved=save_list(self.service,{'title':'所有筛选题目'})['list']
        rows=[dict(self.library.rows[0],id=f'large::{i}',url=f'https://www.luogu.com.cn/problem/P{10000+i}') for i in range(1300)]
        with patch.object(self.service,'_library',return_value=rows) as reader:
            result=add_problems(self.service,{'listIds':[saved['id']],'problemIds':[row['id'] for row in rows]})
        self.assertEqual(reader.call_count,1)
        self.assertEqual(result['added'][saved['id']],1300)
        self.assertEqual(len(read_lists(self.service)[0]['problems']),1300)
