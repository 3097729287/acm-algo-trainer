import io
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from preferences import read_preferences, save_preferences
from training import TrainingService, ServiceError
from leaderboard import RankingRequestError
import test_training as fixtures


class UICompatibilityTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown

    def test_page_opacity_roundtrip_does_not_replace_other_user_data(self):
        self.service.start_training('fixture::A')
        self.service.save_draft('fixture::A', 'int main() { return 7; }')
        saved={'favorites':['fixture::A'],'views':[{'id':'v','name':'saved','filters':{'min':1000}}],
               'panelOpacity':76,'pageOpacities':{'library':0,'statement':45,'editor':90}}
        save_preferences(self.service,{'preferences':saved})
        self.service.close()
        self.service=TrainingService(self.library,self.db,self.assets,self.judge,self.clock,self.root/'backups')
        self.assertEqual(read_preferences(self.service)['preferences'],saved)
        self.assertEqual(self.service.problem('fixture::A')['draft'],'int main() { return 7; }')
        for opacities in ({'library':101},{'editor':-1},{'unknown':70},{'library':True},[]):
            with self.assertRaises(ServiceError):save_preferences(self.service,{'preferences':{'pageOpacities':opacities}})

    def test_old_shared_service_has_no_fake_local_hearts(self):
        client=self.service.leaderboard
        profile={'endpoint':'http://127.0.0.1:18000','auth_token':'fixture','user_id':'id'}
        with patch.object(self.service,'_ranking_profile',return_value=profile), patch.object(client,'_request',side_effect=RankingRequestError(404,'old service')):
            self.assertFalse(client.social()['available'])
            with self.assertRaises(ServiceError) as issue:client.social({'targetId':'other'},'likes')
            self.assertEqual(issue.exception.status,503)

    def test_read_boundary_forwards_only_batch_ids_or_literal_all(self):
        client=self.service.leaderboard
        profile={'endpoint':'http://127.0.0.1:18000','auth_token':'fixture','user_id':'id'}
        with patch.object(self.service,'_ranking_profile',return_value=profile),patch.object(client,'_request',return_value={'ok':True}) as request:
            for selection in ({'all':True},{'ids':[]},{'ids':['123e4567-e89b-42d3-a456-426614174000']}):
                self.assertEqual(client.social(selection,'read'),{'ok':True})
                request.assert_called_with(profile,'POST','/v1/social/read',selection)
            request.reset_mock()
            for selection in ({'all':False},{'all':1},{'all':'true'},{'all':None},{'all':True,'ids':[]},
                              {'all':True,'userId':'other'},{'all':True,'targetId':'other'},
                              {'all':True,'recipientId':'other'},{'ids':[],'actorId':'other'},{}):
                with self.subTest(selection=selection),self.assertRaises(ServiceError) as issue:
                    client.social(selection,'read')
                self.assertEqual(issue.exception.status,400)
            request.assert_not_called()

    def test_social_snapshot_has_a_bounded_larger_response_budget_only_for_its_get(self):
        client=self.service.leaderboard
        profile={'endpoint':'http://127.0.0.1:18000','auth_token':'fixture','user_id':'id'}
        person={'userId':'123e4567-e89b-42d3-a456-426614174000','nickname':'🐈'*32}
        notification={'id':person['userId'],'kind':'comment','actor':person,'recipient':person,
                      'text':'🐈'*500,'createdAt':'2026-10-20T12:00:00.000Z','read':False}
        activity={key:notification[key] for key in ('id','actor','recipient','createdAt')}
        activity['kind']='like'
        value={'available':True,'protocol':1,'totalLikes':30,'unreadCount':100,
               'notifications':[dict(notification,id=f'123e4567-e89b-42d3-a456-{index:012d}') for index in range(100)],
               'activity':[activity for _ in range(30)]}
        payload=json.dumps(value,ensure_ascii=False).encode('utf-8')
        self.assertGreater(len(payload),256*1024)
        read_sizes=[]
        class Response(io.BytesIO):
            def read(self,size=-1):
                read_sizes.append(size)
                return super().read(size)
        def send(raw,method='GET',path='/v1/social'):
            opener=SimpleNamespace(open=lambda *args,**kwargs:Response(raw))
            client.opener_endpoint=None
            with patch('leaderboard.service_opener',return_value=opener):
                return client._request(profile,method,path)
        self.assertEqual(send(payload),value)
        self.assertEqual(read_sizes[-1],1024*1024+1)
        for method,path in (('GET','/v1/profile'),('POST','/v1/social'),('GET','/v1/social?other=1')):
            with self.subTest(method=method,path=path),self.assertLogs('tb.ranking',level='WARNING'),self.assertRaises(RuntimeError):
                send(payload,method,path)
            self.assertEqual(read_sizes[-1],256*1024+1)
        with self.assertLogs('tb.ranking',level='WARNING'),self.assertRaises(RuntimeError):
            send(b'{"oversized":"'+b'x'*(1024*1024)+b'"}')
        self.assertEqual(read_sizes[-1],1024*1024+1)

    def test_preview_rotates_across_drafts_and_persisted_papers_after_restart(self):
        base=self.library.rows[0]
        self.library.rows=[dict(base,id=f'rotate::{level}-{variant}',url=f'https://example.com/{level}-{variant}',difficulty=800+level*300,tags=['linear DP' if level==1 else 'BFS' if level==2 else '模拟']) for level in range(4) for variant in range(4)]
        config={'count':4,'min':800,'max':1700,'duration':120}
        first=self.service.preview_contest(config)['plan']
        second=self.service.preview_contest(config)['plan']
        first_ids={slot['id'] for slot in first['slots']}
        second_ids={slot['id'] for slot in second['slots']}
        self.assertFalse(first_ids & second_ids)
        self.service.start_contest({'previewId':second['previewId'],'ids':list(slot['id'] for slot in second['slots']),'duration':120})
        self.service.finish_contest(self.service.workspace()['activeContest']['id'])
        self.service.close()
        self.service=TrainingService(self.library,self.db,self.assets,self.judge,self.clock,self.root/'backups')
        third=self.service.preview_contest(config)['plan']
        self.assertFalse(second_ids & {slot['id'] for slot in third['slots']})
        self.assertEqual(len(third['slots']),4)
        self.assertNotIn('difficulty',third['slots'][0])


if __name__ == '__main__':unittest.main()
