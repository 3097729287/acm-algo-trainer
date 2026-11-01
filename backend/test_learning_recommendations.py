"""Learning proof is official participation, independent of the rating window."""
import datetime as dt
import unittest
from insights import build_insights

NOW=dt.datetime(2026,11,2,12,tzinfo=dt.timezone.utc)

def row(index,**extra):
    return {'id':str(index),'title':'Learning task','platform':'Codeforces','url':f'https://codeforces.com/contest/900/problem/{index}',
            'difficulty':1000,'difficultySource':'Codeforces 官方 rating','tags':['并查集'],**extra}

def receipt(index,**extra):
    return {'id':'receipt-'+str(index),'problem_id':str(index),'mode':'submit','scope':'official','verdict':'AC',
            'submitted_at':'2026-11-01T10:00:00Z','finished_at':'2026-11-01T10:01:00Z','code':'private verified source',
            'solution_seen':0,**extra}

class LearningRecommendationTests(unittest.TestCase):
    def build(self,rows,records,workspace=None):
        return build_insights(rows,records,[],workspace or {},{},NOW)

    def test_unrated_official_learning_is_preserved_without_inventing_rating(self):
        value=self.build([row('native',platform='Luogu',difficulty=None,difficultySource='洛谷原生档位')],[receipt('native')])
        proof=value['learningEvidence'];self.assertEqual(proof['method'],'verified-official-learning-v1')
        self.assertEqual(len(proof['records']),1);self.assertTrue(proof['records'][0]['solved'])
        self.assertIsNone(value['assessment']['abilityScore']);self.assertEqual(value['assessment']['evidence'],[])
        self.assertTrue(all('code' not in fact for fact in proof['records']));self.assertNotIn('private verified source',str(proof))

    def test_assistance_unknown_independence_local_and_future_results_never_prove_learning(self):
        changes=[{'solution_seen':1},{'solution_seen':None},{'scope':'local'},{'code':''},{'verdict':'CE'},
                 {'submitted_at':'2026-11-03T00:00:00Z','finished_at':'2026-11-03T00:01:00Z'}]
        for change in changes:
            with self.subTest(change=change):self.assertEqual(self.build([row(1)],[receipt(1,**change)])['learningEvidence']['records'],[])

    def test_original_aliases_and_retries_remain_one_episode_with_failures(self):
        rows=[row('a',aliasIds=['alias']),row('b',url='https://codeforces.com/problemset/problem/900/a')]
        records=[receipt('alias',id='first',verdict='WA',submitted_at='2026-10-31T10:00:00Z',finished_at='2026-10-31T10:01:00Z'),receipt('a'),receipt('b')]
        facts=self.build(rows,records)['learningEvidence']['records'];self.assertEqual(len(facts),1)
        self.assertEqual(facts[0]['failures'],1);self.assertFalse(facts[0]['firstPass']);self.assertTrue(facts[0]['solved'])

    def test_more_than_sixty_real_problems_keep_learning_facts_and_contest_masks_them(self):
        rows=[row(i) for i in range(70)];records=[receipt(i) for i in range(70)]
        value=self.build(rows,records);self.assertEqual(len(value['assessment']['evidence']),60)
        self.assertEqual(len(value['learningEvidence']['records']),70)
        masked=self.build(rows,records,{'activeContest':{'id':'running'}})
        self.assertEqual(masked['learningEvidence']['records'],[]);self.assertEqual(masked['assessment']['evidence'],[])

    def test_projection_is_bounded_and_contains_only_public_problem_and_learning_fields(self):
        rows=[row(i,difficulty=None) for i in range(520)];records=[receipt(i) for i in range(520)]
        proof=self.build(rows,records)['learningEvidence'];self.assertEqual(len(proof['records']),512)
        allowed={'id','problemId','solved','date','failures','firstPass','rated','independentKnown','scope'}
        for fact in proof['records']:self.assertEqual(set(fact),allowed)

if __name__=='__main__':unittest.main()
