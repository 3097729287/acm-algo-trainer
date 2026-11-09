"""Actual local Python HTTP relay -> disposable production Node HTTP adapter."""
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import test_training as fixtures
from test_official_v4 import NODE
from leaderboard import RankingRequestError


class PresenceLeaseRelayTests(unittest.TestCase):
    request=fixtures.HTTPTests.request

    def setUp(self):
        fixtures.HTTPTests.setUp(self)
        self.addCleanup(fixtures.HTTPTests.tearDown,self)
        root=Path(__file__).resolve().parents[1]
        command=[NODE]
        if os.environ.get('TB_PRESENCE_NODE_LOADER'):command+=['--loader',Path(os.environ['TB_PRESENCE_NODE_LOADER']).resolve().as_uri()]
        command+=[str(root/'server/leaderboard/tests/presence-relay-fixture.mjs')]
        self.node=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8')
        self.addCleanup(self.close_node)
        line=self.node.stdout.readline()
        if not line:raise AssertionError('Local Node fixture did not start: '+self.node.stderr.read()[-1200:])
        hello=json.loads(line);self.assertTrue(hello['ready']);self.ids=hello['ids'];self.actor=0;self.forwarded=[]
        self.profile=patch.object(self.server.training,'_ranking_profile',side_effect=lambda:{'user_id':self.ids[self.actor],'endpoint':'https://fixture.invalid','auth_token':'not-a-real-token'})
        self.profile.start();self.addCleanup(self.profile.stop)
        def transport(profile,method,path,value):
            self.forwarded.append((profile['user_id'],method,path,dict(value)))
            result=self.ipc({'actor':self.ids.index(profile['user_id']),'path':path,'value':value})
            if result['status']!=200:raise RankingRequestError(result['status'],result['value'].get('error','fixture rejected'))
            return result['value']
        self.transport=patch.object(self.server.training.leaderboard,'_request',side_effect=transport);self.transport.start();self.addCleanup(self.transport.stop)

    def ipc(self,value):
        self.node.stdin.write(json.dumps(value)+'\n');self.node.stdin.flush()
        return json.loads(self.node.stdout.readline())

    def close_node(self):
        self.node.stdin.close()
        try:self.node.wait(timeout=4)
        except subprocess.TimeoutExpired:self.node.kill();self.node.wait(timeout=2)
        self.node.stdout.close();self.node.stderr.close()

    def test_native_relay_keeps_ticket_and_old_close_after_account_switch_cannot_write_new_owner(self):
        status,prepared=self.request('POST','/api/presence',{'activity':'problem','presencePhase':'prepare','presenceOwner':self.ids[0]})
        self.assertEqual(status,200)
        ticket={key:prepared[key] for key in ['presenceLease','presenceExpected']}
        status,value=self.request('POST','/api/presence',{'activity':'problem','presencePhase':'activate','presenceOwner':self.ids[0],**ticket})
        self.assertEqual(status,200);self.assertEqual(value['presenceState'],'active')
        self.actor=1;before=self.ipc({'kind':'row','actor':1});forwarded=len(self.forwarded)
        status,_=self.request('POST','/api/presence',{'activity':'offline','presencePhase':'close','presenceOwner':self.ids[0],**ticket})
        self.assertEqual(status,409)
        self.assertEqual(self.ipc({'kind':'row','actor':1}),before)
        self.assertEqual(len(self.forwarded),forwarded);self.assertEqual(self.forwarded[-1][-1]['presenceLease'],ticket['presenceLease']);self.assertNotIn('presenceOwner',self.forwarded[-1][-1])
        self.actor=0;status,value=self.request('POST','/api/presence',{'activity':'idle','presencePhase':'beat','presenceOwner':self.ids[0],**ticket})
        self.assertEqual(status,200);self.assertEqual(value['idleUsers'],[{'userId':self.ids[0],'activity':'idle'}])

    def test_legacy_payload_still_relays_and_future_time_or_unrelated_fields_are_rejected_locally(self):
        self.assertEqual(self.request('POST','/api/presence',{'activity':'lecture'})[0],200)
        before=len(self.forwarded)
        for payload in [{'activity':'online','clientNow':999999999999999},{'activity':'online','title':'private'},{'presencePhase':'prepare'},{'activity':'online','presencePhase':'prepare'}]:
            self.assertEqual(self.request('POST','/api/presence',payload)[0],400)
        self.assertEqual(len(self.forwarded),before)


if __name__=='__main__':unittest.main()
