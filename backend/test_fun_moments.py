"""Real account ledgers, hidden display and confirmed-feature evidence; no OJ I/O."""
from concurrent.futures import ThreadPoolExecutor
import json
import unittest
from unittest.mock import patch

from fun_moments import from_facts,confirmed_gameplay,confirmed_wiki_visit
from fun_moment_definitions import MOMENTS
from progression import ACHIEVEMENT_DEFINITIONS
import test_training as fixtures


class FunMomentTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown
    accept=fixtures.ServiceTests.accept

    def records(self):return [dict(row) for row in self.service.connection.execute('SELECT * FROM submissions ORDER BY submitted_at,rowid')]

    def test_secret_condition_is_absent_until_real_completion_and_claim_is_once(self):
        self.assertNotIn('moment-semicolon',{x['id'] for x in self.service.insights()['achievements']})
        self.accept(verdict='CE',code='int main(){return 0}')
        self.clock.advance(minutes=1)
        self.accept(code='int main(){return 0;}')
        before=self.service.insights();items={x['id']:x for x in before['achievements']}
        self.assertTrue(items['moment-semicolon']['hidden']);self.assertTrue(items['moment-semicolon']['unlocked'])
        self.assertEqual(before['growth']['achievementXp'],0)
        with ThreadPoolExecutor(max_workers=5) as pool:claims=list(pool.map(lambda _:self.service.claim_achievement('moment-semicolon',compact=True),range(5)))
        self.assertEqual(sum(x['awardedXp'] for x in claims),15)
        self.assertEqual(self.service.connection.execute("SELECT COUNT(*) FROM achievement_xp_claims WHERE achievement_id='moment-semicolon'").fetchone()[0],1)
        with self.service._write() as db:db.execute('DELETE FROM submissions')
        self.clock.advance(days=2)
        after={x['id']:x for x in self.service.insights()['achievements']}
        self.assertTrue(after['moment-semicolon']['unlocked']);self.assertTrue(after['moment-semicolon']['rewardClaimed'])
        self.assertEqual(self.service.claim_achievement('moment-semicolon',compact=True)['awardedXp'],0)

    def test_local_samples_missing_sources_and_unrelated_problems_do_not_fake_official_moments(self):
        self.accept(verdict='CE',code='int main(){return 0}')
        self.clock.advance(seconds=1);self.accept(identity='fixture::B',code='int main(){return 0;}')
        values={x['id']:x for x in from_facts(self.service,self.records())}
        self.assertFalse(values['moment-semicolon']['unlocked']);self.assertFalse(values['moment-rebound']['unlocked'])
        records=self.records();records[1]['problem_id']='fixture::A';records[1]['scope']='samples'
        self.assertFalse(next(x for x in from_facts(self.service,records) if x['id']=='moment-semicolon')['unlocked'])
        records[1]['scope']='official';records[0]['code']=''
        self.assertFalse(next(x for x in from_facts(self.service,records) if x['id']=='moment-semicolon')['unlocked'])

    def test_confirmed_inventory_and_duel_proofs_are_owner_bound_and_not_repeated_by_polling(self):
        owner=self.service._ranking_profile()['user_id']
        rarities=['common','rare','epic','legendary','common']
        view={'owner':owner,'catalogue':[{'id':str(i),'rarity':r} for i,r in enumerate(rarities)],
              'units':[{'id':'unit'+str(i),'stickerId':str(i),'placement':{'x':.5,'y':.5,'angle':180 if i==0 else 0}} for i in range(5)]}
        confirmed_gameplay(self.service,{**view,'owner':'another-owner'},'recycle')
        self.assertEqual(self.service.connection.execute("SELECT COUNT(*) FROM account_preferences WHERE key LIKE 'achievement-unlock:moment-%'").fetchone()[0],0)
        for _ in range(4):confirmed_gameplay(self.service,view,'recycle')
        self.assertEqual(self.service.connection.execute("SELECT COUNT(*) FROM account_preferences WHERE key LIKE 'achievement-unlock:moment-%'").fetchone()[0],4)
        state=self.service.insights();items={x['id']:x for x in state['achievements']}
        self.assertTrue(all(items['moment-'+name]['unlocked'] for name in ('gallery','rainbow','upside-down','returned')))
        # A draw with no accepted submissions is not the hidden same-second AC.
        room={'id':'real-fixture-room','status':'finished','winner':None,'players':[{'owner':owner,'acceptedAt':None},{'owner':'peer','acceptedAt':None}]}
        confirmed_gameplay(self.service,{'owner':owner,'match':room})
        self.assertNotIn('moment-duel-tie',{x['id'] for x in self.service.insights()['achievements']})
        for player in room['players']:player['acceptedAt']=123000
        confirmed_gameplay(self.service,{'owner':owner,'match':room})
        self.assertTrue(next(x for x in self.service.insights()['achievements'] if x['id']=='moment-duel-tie')['unlocked'])

    def test_wiki_visits_are_distinct_categories_and_do_not_claim_reading_or_mastery(self):
        for identity,category in [('one','图论'),('two','图论'),('three','数学')]:confirmed_wiki_visit(self.service,{'id':identity,'category':category})
        self.assertFalse(next(x for x in from_facts(self.service,[]) if x['id']=='moment-wiki-trip')['unlocked'])
        confirmed_wiki_visit(self.service,{'id':'four','category':'字符串'})
        self.assertTrue(next(x for x in from_facts(self.service,[]) if x['id']=='moment-wiki-trip')['unlocked'])
        self.assertEqual(self.service.connection.execute('SELECT COUNT(*) FROM submissions').fetchone()[0],0)
        self.assertTrue(all(identity in ACHIEVEMENT_DEFINITIONS for identity in MOMENTS))

    def test_42_requires_an_actually_finished_run_with_exact_output(self):
        self.accept()
        with self.service._write() as db:
            db.execute("UPDATE submissions SET mode='run',verdict='RUN_OK',output='42 extra'")
        self.assertFalse(next(x for x in from_facts(self.service,[]) if x['id']=='moment-42')['unlocked'])
        with self.service._write() as db:db.execute("UPDATE submissions SET output='42'||char(10)")
        value=next(x for x in from_facts(self.service,[]) if x['id']=='moment-42')
        self.assertTrue(value['unlocked']);self.assertTrue(value['hidden'])


if __name__=='__main__':unittest.main()
