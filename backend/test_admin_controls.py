"""Admin display previews never manufacture ordinary progress or reward claims."""
import json
import unittest
from admin import controls
import test_v130 as fixtures


class AdminPreviewTests(unittest.TestCase):
    setUp=fixtures.WorkbenchUpdateTests.setUp
    tearDown=fixtures.WorkbenchUpdateTests.tearDown

    def ledgers(self,service):
        names={r[0] for r in service.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        protected=['submissions','training','achievement_xp_claims','daily_missions','ranking_reward_totals','ranking_reward_claims','review_xp_claims']
        return {name:[tuple(row) for row in service.connection.execute('SELECT * FROM '+name+' ORDER BY rowid')] for name in protected if name in names}

    def test_default_and_manual_levels_are_local_previews_without_reward_ledger_writes(self):
        before_user=self.user.insights();self.admin.insights()
        user_ledger=self.ledgers(self.user);admin_ledger=self.ledgers(self.admin)
        self.assertTrue(controls(self.admin)['allAchievements'])
        for level in [1,2,42,100]:
            controls(self.admin,{'level':level,'tier':3,'allAchievements':True})
            value=self.admin.insights()
            self.assertEqual(value['growth']['level'],level)
            self.assertTrue(all(a['unlocked'] and a['rewardClaimed'] and a['adminGranted'] for a in value['achievements']))
            self.assertEqual(self.ledgers(self.admin),admin_ledger)
            self.assertEqual(self.ledgers(self.user),user_ledger)
            # Confirmation authority revisions may advance during an ordinary
            # read; the actual XP, levels, component rewards and ledgers cannot.
            self.assertEqual({k:v for k,v in self.user.insights()['growth'].items() if k!='authority'},
                             {k:v for k,v in before_user['growth'].items() if k!='authority'})

    def test_old_false_migrates_once_then_an_explicit_off_survives_reload(self):
        with self.admin._write() as db:
            db.execute("INSERT INTO account_preferences VALUES('admin-controls',?,?)",(json.dumps({'level':7,'tier':2,'allAchievements':False,'rankLadderVersion':2}),'2026-10-01'))
        before=self.admin.connection.total_changes
        self.assertTrue(controls(self.admin)['allAchievements'])
        self.assertEqual(self.admin.connection.total_changes,before,'Display migration does not issue reward/XP writes')
        self.assertTrue(all(a['unlocked'] for a in self.admin.insights()['achievements']))
        controls(self.admin,{'level':7,'tier':2,'allAchievements':False})
        stored=json.loads(self.admin.connection.execute("SELECT value FROM account_preferences WHERE key='admin-controls'").fetchone()[0])
        self.assertEqual(stored['previewVersion'],1)
        self.assertFalse(controls(self.admin)['allAchievements'])
        self.admin.close()
        from training import TrainingService
        from test_training import Assets,Judge
        self.admin=TrainingService(self.library,self.root/'admin'/'personal.sqlite3',assets=Assets(self.library),judge=Judge(),clock=lambda:self.clock,admin_mode=True)
        self.assertFalse(controls(self.admin)['allAchievements'])
        self.assertTrue(any(not a['unlocked'] for a in self.admin.insights()['achievements']))
