import copy
import json
import unittest
from unittest.mock import patch

import test_training as fixtures
from account_sync import baselines,merge_states
from experience_challenge import update,read,KEY as ASSESSMENT_KEY
from starter_pacing import KEY,BEGINNER_COSTS,costs,preserve_rows
from tb_rank import growth,LEVEL_COSTS

class StarterPacingTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown

    def test_new_beginner_progresses_at_200_600_1200_2000_without_xp_rewrite(self):
        initial=self.service.insights()['growth']
        chosen=update(self.service,{'action':'choose','choice':'beginner'})['growth']
        self.assertEqual(chosen['totalXp'],initial['totalXp'])
        self.assertEqual(chosen['levelCosts'][:4],[200,400,600,800])
        for xp,level in [(199,1),(200,2),(599,2),(600,3),(1199,3),(1200,4),(1999,4),(2000,5)]:
            value=growth(xp,level_costs=costs(self.service))
            self.assertEqual(value['level'],level);self.assertEqual(value['totalXp'],xp)
        self.assertEqual(chosen['rankUnlockXp'],2000)

    def test_legacy_choice_and_existing_level_are_not_migrated(self):
        state=read(self.service);state.update(choice='beginner',seenVersion=1)
        with self.service._write() as db:db.execute('INSERT INTO account_preferences VALUES(?,?,?)',(ASSESSMENT_KEY,json.dumps(state),self.clock().isoformat()))
        update(self.service,{'action':'choose','choice':'beginner'})
        self.assertEqual(costs(self.service),LEVEL_COSTS)
        with self.service._write() as db:db.execute('DELETE FROM account_preferences WHERE key=?',(ASSESSMENT_KEY,))
        with patch.object(self.service,'insights',return_value={'growth':{'level':3,'experienceChallenge':{'eligible':True}}}):
            update(self.service,{'action':'choose','choice':'beginner'})
        self.assertEqual(costs(self.service),LEVEL_COSTS)

    def test_experienced_choice_keeps_the_existing_test_and_500_xp_gate(self):
        chosen=update(self.service,{'action':'choose','choice':'experienced'})['growth']
        self.assertEqual(costs(self.service),LEVEL_COSTS)
        self.assertEqual(chosen['rankUnlockXp'],500)
        self.assertEqual(growth(500,level_costs=costs(self.service))['level'],5)

    def test_curve_survives_older_device_snapshots_and_is_owner_scoped(self):
        update(self.service,{'action':'choose','choice':'beginner'})
        row=dict(self.service.connection.execute('SELECT * FROM account_preferences WHERE key=?',(KEY,)).fetchone())
        state={'version':1,'tables':{'account_preferences':[row]},'publicAccounts':{}}
        empty=copy.deepcopy(state);empty['tables']['account_preferences']=[]
        for local,remote in [(state,empty),(empty,state)]:
            joined=merge_states(local,remote,baselines(state))
            self.assertEqual(joined['tables']['account_preferences'],[row])
        preserved,changed=preserve_rows(self.service,[])
        self.assertTrue(changed);self.assertEqual(preserved,[row])
        forged=json.loads(row['value']);forged['owner']='another-account'
        with self.service._write() as db:db.execute('UPDATE account_preferences SET value=? WHERE key=?',(json.dumps(forged),KEY))
        self.assertEqual(costs(self.service),LEVEL_COSTS)

if __name__=='__main__':unittest.main()
