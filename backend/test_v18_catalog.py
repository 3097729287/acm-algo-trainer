import datetime as dt
import unittest
from unittest.mock import patch

from contest_names import contest_name, normalize_row
from contest_policy import apply_visibility
from contest_translations import xcpc_name
from goals import shared_contest_plan
import public_platforms as P
from test_integrations import Client
import test_integrations as fixtures
from xcpc_discovery import discover_gyms, historical, Roster


class CataloguePolicyTests(unittest.TestCase):
    def test_retirement_is_limited_to_auto_imports_and_preserves_the_record(self):
        old={'id':'old::A','source':'xcpc-codeforces','xcpcYear':2016,'title':'Old exercise'}
        hidden=apply_visibility(old)
        self.assertTrue(hidden['catalogHidden'])
        self.assertEqual(hidden['id'],old['id'])
        self.assertNotIn('catalogHidden',old)
        self.assertNotIn('catalogHidden',apply_visibility({**old,'source':'user-import'}))
        self.assertNotIn('catalogHidden',apply_visibility({**old,'xcpcYear':2017}))

    def test_original_yinchuan_date_wins_over_mirror_upload(self):
        row=normalize_row({'id':'preserved::A','contest':'ICPC 2019 银川区域赛','collectionSource':'https://www.luogu.com.cn/contest/358583','startedAt':'2026-10-07T00:00:00+00:00','contestDate':'2026-10-07T00:00:00+00:00'})
        self.assertTrue(row['contestDate'].startswith('2019-10-20'))
        self.assertIn('xcpcio',row['contestDateSource'])
        self.assertEqual(row['id'],'preserved::A')

    def test_chinese_names_preserve_country_stage_and_divisions(self):
        self.assertEqual(contest_name('ABC 471'),'ABC 471')
        self.assertEqual(contest_name('Codeforces Round 1124 (Div. 1)'),'Div.1 1124')
        self.assertIn('乌拉尔',xcpc_name('2023-2024 Квалификационный тур Уральского четвертьфинала ICPC'))
        self.assertIn('资格',xcpc_name('2023-2024 Квалификационный тур Уральского четвертьфинала ICPC'))
        self.assertNotEqual(xcpc_name('2024 ICPC Asia Taiwan Online Programming Contest'),xcpc_name('2024 ICPC Asia Japan Online First-Round Contest'))
        self.assertIn('部分题目',xcpc_name('ICPC Thailand National Contest 2025 (Partial)'))

    def test_only_curated_regular_rounds_and_new_eligible_gyms_are_discovered(self):
        now=dt.datetime(2026,10,15,tzinfo=dt.timezone.utc)
        policy={'curatedCodeforcesContests':[10],'knownGymContests':[101700],'excludedGymContests':[],'discoverAuthorizedSeries':False}
        contests=[{'id':i,'name':'Codeforces Round '+str(i)+' (Div. 2)','phase':'FINISHED','startTimeSeconds':1,'durationSeconds':100} for i in (10,11)]
        gyms=[{'id':101700,'name':'2017 ICPC Asia Xian','phase':'FINISHED'},
              {'id':101600,'name':'2016 ICPC Asia Xian','phase':'FINISHED'},
              {'id':106800,'name':'2026 ICPC Asia Xian','phase':'FINISHED','difficulty':4},
              {'id':106900,'name':'2027 ICPC Asia Xian','phase':'FINISHED'}]
        client=Client({'https://codeforces.com/api/contest.list?gym=false':{'status':'OK','result':contests},
                       'https://codeforces.com/api/problemset.problems':{'status':'OK','result':{'problems':[{'contestId':i,'index':'A','name':'Task','rating':1200} for i in (10,11)]}},
                       'https://codeforces.com/api/contest.list?gym=true':{'status':'OK','result':gyms},
                       'https://codeforces.com/gym/106800':'<a href="/gym/106800/problem/A">A</a><a href="/gym/106800/problem/A">Real task name</a>'})
        with patch('contest_policy.policy',return_value=policy):
            rows,pending,_=P.discover_curated_cf(client,now)
        self.assertEqual({r['contestId'] for r in rows},{'10','106800'})
        self.assertFalse(pending)
        gym=next(r for r in rows if r['contestId']=='106800')
        self.assertIsNone(gym['contestDate'])
        self.assertEqual(gym['contestDifficulty'],4)
        self.assertIsNone(gym['difficulty'])
        self.assertNotIn('https://codeforces.com/gym/101600',client.calls)

    def test_shared_weekly_plan_takes_each_strongest_requirement_once(self):
        first={'id':'one','currentRating':1000,'contestPlan':[{'contest':'Codeforces Div.3','target':4,'problems':'A–D'},{'contest':'牛客周赛','target':1,'problems':'A–D'}]}
        second={'id':'two','currentRating':1600,'contestPlan':[{'contest':'Codeforces Div.3','target':2,'problems':'C–F'},{'contest':'牛客周赛','target':5,'problems':'C–F'}]}
        plan=shared_contest_plan([first,second])
        self.assertEqual(plan['total'],9)
        self.assertEqual([(r['target'],r['problems']) for r in plan['contests']],[(4,'C–F'),(5,'C–F')])
        self.assertEqual(len(plan['contests']),2)
        self.assertEqual(shared_contest_plan([first,{**second,'workloadCompleted':True}])['total'],5)

    def test_shared_questions_exclude_solved_and_retired_tasks_and_keep_current_range(self):
        goal={'id':'one','currentRating':1600,'contestPlan':[{'contest':'Codeforces Div.3','target':2,'problems':'C–F'}]}
        rows=[{'id':'p'+letter,'platform':'Codeforces','contest':'Div.3 1124','problem':letter,'title':'Task '+letter,'url':'https://codeforces.com/contest/1/problem/'+letter,'difficulty':1500,'contestDate':'2026-10-01'} for letter in 'ABCDEF']
        rows[-1]['catalogHidden']=True
        plan=shared_contest_plan([goal],rows,{'codeforces.com/contest/1/problem/C'})
        self.assertEqual([r['problem'] for r in plan['contests'][0]['questions']],['D','E'])


class ReadAllTests(unittest.TestCase):
    setUp=fixtures.IntegrationTests.setUp
    tearDown=fixtures.IntegrationTests.tearDown

    def test_bulk_read_is_persistent_idempotent_and_keeps_notification_targets(self):
        self.service.state['notifications']=[{'id':'one','read':False,'problemIds':['preserved::A']},{'id':'two','read':True,'problemUrls':['https://example.com/a']}]
        with patch.object(self.service,'_save',wraps=self.service._save) as save:
            result=self.service.dismiss_all()
            self.service.dismiss_all()
            self.assertEqual(save.call_count,1)
        self.assertTrue(all(n['read'] for n in result['notifications']))
        self.assertEqual(result['notifications'][0]['problemIds'],['preserved::A'])
        self.assertEqual(result['notifications'][1]['problemUrls'],['https://example.com/a'])


if __name__=='__main__':unittest.main()
