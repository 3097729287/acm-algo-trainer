"""Native eligibility and stable reward receipts, without real account calls."""
import json
import unittest
from unittest.mock import patch
import test_training as fixtures
from fun_moments import confirmed_gameplay,from_facts
from sticker_rewards import achievement_sticker,grant_pending
from progression import ACHIEVEMENT_DEFINITIONS

class StickerRewardTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown

    def test_unearned_stickers_are_not_granted_and_level_sync_is_retry_safe(self):
        calls=[]
        with patch.object(self.service,'public_progress',return_value={'level':0}),patch('gameplay._request') as network:
            grant_pending(self.service);network.assert_not_called()
        def received(*args,**kwargs):calls.append((args[2],args[3]));return {'owner':self.service._ranking_profile()['user_id']}
        with patch.object(self.service,'public_progress',return_value={'level':13}),patch('gameplay._request',side_effect=received):
            grant_pending(self.service);grant_pending(self.service)
        self.assertEqual(len(calls),1);self.assertEqual(calls[0][0],'/v1/stickers/levels');self.assertEqual(calls[0][1]['level'],13)
        with patch.object(self.service,'public_progress',return_value={'level':14}),patch('gameplay._request',side_effect=RuntimeError('lost response')):
            with self.assertRaises(RuntimeError):grant_pending(self.service)
        self.assertFalse(self.service.connection.execute("SELECT 1 FROM account_preferences WHERE key='sticker-levels-v4:14'").fetchone())

    def test_fixed_reward_requires_the_committed_achievement_claim(self):
        self.assertEqual(achievement_sticker('leader-tease')['rarity'],'legendary')
        self.assertEqual(ACHIEVEMENT_DEFINITIONS['leader-tease']['rewardXp'],0)
        with self.service._write() as db:db.execute('INSERT INTO achievement_xp_claims VALUES(?,?,?,?)',('leader-tease',None,20,self.clock().isoformat()))
        calls=[]
        with patch.object(self.service,'public_progress',return_value={'level':1}),patch('gameplay._request',side_effect=lambda *args,**kwargs:calls.append(args[3]) or {}):
            grant_pending(self.service);grant_pending(self.service)
        self.assertEqual(len(calls),2);self.assertEqual([call['achievementId'] for call in calls if 'achievementId' in call],['leader-tease'])
        self.assertEqual(self.service.connection.execute("SELECT awarded_xp FROM achievement_xp_claims WHERE achievement_id='leader-tease'").fetchone()[0],20,'Prior earned XP is retained')

    def test_collection_rewards_count_distinct_confirmed_stickers_and_keep_completed_facts(self):
        owner=self.service._ranking_profile()['user_id']
        catalogue=[{'id':'verified:'+str(i),'rarity':'rare'} for i in range(24)]
        units=[{'id':'unit:'+str(i),'stickerId':item['id']} for i,item in enumerate(catalogue)]
        confirmed_gameplay(self.service,{'owner':owner,'catalogue':catalogue,'units':units+units,'boxes':{}})
        facts={x['id']:x for x in from_facts(self.service,[])}
        self.assertTrue(facts['moment-collection-12']['unlocked']);self.assertTrue(facts['moment-collection-24']['unlocked'])
        confirmed_gameplay(self.service,{'owner':owner,'catalogue':catalogue,'units':[],'boxes':{}})
        facts={x['id']:x for x in from_facts(self.service,[])};self.assertTrue(facts['moment-collection-24']['unlocked'])
        self.assertEqual(achievement_sticker('streak-365')['shape'],'yearbadge')

    def test_box_and_gift_facts_are_owner_bound_and_survive_repeated_reads(self):
        owner=self.service._ranking_profile()['user_id']
        view={'owner':owner,'units':[],'catalogue':[],'boxes':{'level:'+str(i):{'openedAt':1,'drops':[{'rarity':kind} for kind in ['common','rare','epic','legendary']]} for i in range(5,15)},'giftStats':{'sent':15,'recipients':10,'received':1}}
        confirmed_gameplay(self.service,{**view,'owner':'other'})
        self.assertIsNone(self.service.connection.execute("SELECT value FROM account_preferences WHERE key='gameplay-moments-v1'").fetchone())
        confirmed_gameplay(self.service,view)
        first=self.service.connection.execute("SELECT value FROM account_preferences WHERE key='gameplay-moments-v1'").fetchone()[0]
        self.clock.advance(days=1);confirmed_gameplay(self.service,view)
        self.assertEqual(first,self.service.connection.execute("SELECT value FROM account_preferences WHERE key='gameplay-moments-v1'").fetchone()[0])
        items={item['id']:item for item in from_facts(self.service,[])}
        for identity in ['moment-first-gift','moment-gift-five','moment-gift-circle','moment-receive-gift','moment-box-first','moment-box-ten','moment-box-lucky','moment-box-rainbow']:
            self.assertTrue(items[identity]['unlocked'],identity)
        self.assertEqual(items['moment-gift-circle']['progress'],10)
        confirmed_gameplay(self.service,{**view,'boxes':{},'giftStats':{'sent':0,'recipients':0,'received':0}})
        self.assertEqual(json.loads(self.service.connection.execute("SELECT value FROM account_preferences WHERE key='gameplay-moments-v1'").fetchone()[0])['recipients'],10)
