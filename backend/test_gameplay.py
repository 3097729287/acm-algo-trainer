"""Durable daily-reward outbox; no network, personal databases or official submissions."""
import datetime as dt
import json
import unittest
from unittest.mock import patch
import test_training as fixtures
import gameplay

class GameplayTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown
    accept=fixtures.ServiceTests.accept

    def test_ready_and_decline_relay_the_exact_match_identity(self):
        for kind in ('ready','decline'):
            payload={'requestId':'10000000-0000-4000-8000-000000000003','matchId':'isolated-match'}
            response={'owner':self.service._ranking_profile()['user_id'],'status':'ready','match':{'id':'isolated-match'}}
            with patch.object(gameplay,'_request',return_value=response) as network,patch('fun_moments.confirmed_gameplay'):
                self.assertEqual(gameplay.duel(self.service,kind,payload),response)
            network.assert_called_once_with(self.service,'POST','/v1/duels/'+kind,payload,expected_owner=response['owner'])
        with self.assertRaises(gameplay.ServiceError):
            gameplay.duel(self.service,'ready',{'matchId':'another-match','owner':'another-account'})

    def test_new_service_open_box_returns_the_inventory_in_one_network_round_trip(self):
        owner=self.service._ranking_profile()['user_id']
        payload={'requestId':'10000000-0000-4000-8000-000000000004','boxId':'level:7'}
        inventory={'owner':owner,'revision':8,'units':[{'id':'durable-unit'}],'catalogue':[]}
        opening={'id':'level:7','drops':[{'id':'durable-unit'}]}
        with patch.object(gameplay,'_request',return_value={'owner':owner,'inventory':inventory,'opening':opening}) as network,patch('fun_moments.confirmed_gameplay'):
            result=gameplay.stickers(self.service,'open-box',payload)
        network.assert_called_once_with(self.service,'POST','/v1/stickers/open-box',payload,expected_owner=owner)
        self.assertEqual(result['opening'],opening);self.assertEqual(result['units'],inventory['units'])
        with patch.object(gameplay,'_request',return_value={'owner':owner,'inventory':{**inventory,'owner':'another-account'}}):
            with self.assertRaises(gameplay.ServiceError):gameplay.stickers(self.service,'open-box',payload)

    def test_open_box_returns_confirmed_inventory_without_waiting_for_other_rewards(self):
        owner=self.service._ranking_profile()['user_id']
        payload={'requestId':'10000000-0000-4000-8000-000000000001','boxId':'level:5'}
        opening={'id':'level:5','drops':[{'id':'one-unit','stickerId':'leaf-common'}]}
        snapshot={'owner':owner,'revision':2,'units':[{'id':'one-unit'}],'catalogue':[]}
        with patch.object(gameplay,'_request',side_effect=[{'owner':owner,'opening':opening},snapshot]) as network, \
             patch.object(gameplay,'_grant_pending',side_effect=AssertionError('Unrelated outbox must not delay opening')), \
             patch('sticker_rewards.grant_pending',side_effect=AssertionError('Full growth must not delay opening')), \
             patch('fun_moments.confirmed_gameplay') as confirmed:
            result=gameplay.stickers(self.service,'open-box',payload)
        self.assertEqual(result['opening'],opening)
        self.assertEqual(len(result['units']),1)
        self.assertEqual(network.call_count,2)
        self.assertEqual(network.call_args_list[0].args[3],payload)
        self.assertTrue(all(call.kwargs['expected_owner']==owner for call in network.call_args_list))
        confirmed.assert_called_once_with(self.service,result,'open-box')

    def test_lost_inventory_response_retries_the_same_box_operation(self):
        owner=self.service._ranking_profile()['user_id'];payload={'requestId':'10000000-0000-4000-8000-000000000002','boxId':'level:6'}
        mutation={'owner':owner,'opening':{'id':'level:6','drops':[{'id':'durable-unit'}]}}
        with patch.object(gameplay,'_request',side_effect=[mutation,gameplay.ServiceError(503,'lost response'),mutation,{'owner':owner,'revision':4,'units':[{'id':'durable-unit'}]}]) as network,patch('fun_moments.confirmed_gameplay'):
            with self.assertRaises(gameplay.ServiceError):gameplay.stickers(self.service,'open-box',payload)
            result=gameplay.stickers(self.service,'open-box',payload)
        self.assertEqual(network.call_args_list[0].args[3],network.call_args_list[2].args[3])
        self.assertEqual(len(result['units']),1)
        self.assertEqual(result['opening']['drops'][0]['id'],'durable-unit')

    def test_claim_outbox_is_atomic_and_survives_midnight_and_lost_response(self):
        task=next(t for t in self.service.daily_tasks(goal_tasks=[])['tasks'] if t['lane']=='ac')
        self.accept()
        self.service.claim_daily_task(task['id'])
        self.service.claim_daily_task(task['id'])
        rows=self.service.connection.execute("SELECT * FROM account_preferences WHERE key LIKE 'sticker-eligible:%'").fetchall()
        self.assertEqual(len(rows),1)
        day=self.clock().date().isoformat()
        self.clock.advance(days=2)
        calls=[]
        def interrupted(*args,**kwargs):
            calls.append(args[-1]);raise gameplay.ServiceError(503,'isolated lost response')
        with patch.object(gameplay,'_request',side_effect=interrupted):
            with self.assertRaises(gameplay.ServiceError):gameplay._grant_pending(self.service)
        with patch.object(gameplay,'_request',side_effect=lambda *args,**kwargs:calls.append(args[-1]) or {'saved':True}):
            gameplay._grant_pending(self.service)
            gameplay._grant_pending(self.service)
        self.assertEqual(len(calls),2)
        self.assertEqual(calls[0],calls[1])
        self.assertEqual(calls[1]['day'],day)
        self.assertEqual(self.service.connection.execute("SELECT COUNT(*) FROM account_preferences WHERE key LIKE 'sticker-grant:%'").fetchone()[0],1)

    def test_uncompleted_and_sample_results_cannot_create_a_reward(self):
        task=next(t for t in self.service.daily_tasks(goal_tasks=[])['tasks'] if t['lane']=='ac')
        with self.assertRaises(gameplay.ServiceError):self.service.claim_daily_task(task['id'])
        with patch.object(gameplay,'_request') as network:
            gameplay._grant_pending(self.service)
            network.assert_not_called()
        self.assertEqual([gameplay.rarity({'xp':x}) for x in [10,30,60,100]],['common','rare','epic','legendary'])

    def test_a_switched_account_cannot_receive_an_old_owners_outbox(self):
        task=next(t for t in self.service.daily_tasks(goal_tasks=[])['tasks'] if t['lane']=='ac')
        self.accept();self.service.claim_daily_task(task['id'])
        previous=self.service._ranking_profile()
        changed={**previous,'user_id':'different-isolated-owner'}
        with patch.object(self.service,'_ranking_profile',side_effect=[previous,changed]):
            with self.assertRaises(gameplay.ServiceError) as issue:gameplay._grant_pending(self.service)
        self.assertEqual(issue.exception.status,409)
        self.assertEqual(self.service.connection.execute("SELECT COUNT(*) FROM account_preferences WHERE key LIKE 'sticker-grant:%'").fetchone()[0],0)

