import copy,json,unittest
from account_sync import TABLES,encoded,merge_states,recover_legacy_summary

def state(summary,stamp):
    return {'format':'tb-account-state-v1','tables':{name:([{'key':'learning-summary-v1','value':encoded(summary),'updated_at':stamp}] if name=='account_preferences' else []) for name in TABLES},'publicAccounts':{}}

class SummaryMergeTests(unittest.TestCase):
    def test_independent_checks_and_completion_keep_a_single_primary_key(self):
        left=state({'checks':{'left':{'a':True}},'completed':{'old':'hash'},'article':[]},'2026-11-01')
        right=state({'checks':{'right':{'b':True}},'completed':{'new':'hash'},'article':[]},'2026-11-02')
        originals=copy.deepcopy((left,right))
        merged=merge_states(left,right)
        rows=merged['tables']['account_preferences'];self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['key'],'learning-summary-v1')
        value=json.loads(rows[0]['value'])
        self.assertEqual(value['checks'],{'left':{'a':True},'right':{'b':True}})
        self.assertEqual(value['completed'],{'old':'hash','new':'hash'})
        self.assertEqual((left,right),originals)
        again=merge_states(merged,right)
        self.assertEqual(again['tables']['account_preferences'],rows)

    def test_old_duplicate_repairs_both_values_into_exact_conflict_recovery(self):
        left=state({'checks':{'one':{'a':True}},'completed':{},'article':[]},'2026-11-01')
        right=state({'checks':{'two':{'b':True}},'completed':{},'article':[]},'2026-11-02')
        original=copy.deepcopy(left)
        original['tables']['account_preferences']+=right['tables']['account_preferences']
        original['tables']['account_sync_conflicts']=[{'id':'already-preserved','data':'untouched'}]
        before=copy.deepcopy(original);result,repaired=recover_legacy_summary(original)
        self.assertTrue(repaired);self.assertEqual(original,before)
        self.assertEqual(len(result['tables']['account_preferences']),1)
        conflicts=result['tables']['account_sync_conflicts']
        self.assertIn({'id':'already-preserved','data':'untouched'},conflicts)
        preserved=[json.loads(row['data'])['row'] for row in conflicts if row['id']!='already-preserved']
        self.assertCountEqual(preserved,before['tables']['account_preferences'])
        repeated,changed=recover_legacy_summary(result)
        self.assertFalse(changed);self.assertEqual(repeated,result)

if __name__=='__main__':unittest.main()
