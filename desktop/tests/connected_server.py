"""Disposable v4 HTTP fixture. No personal database, credentials or OJ access."""
import json
from pathlib import Path
import sys
import threading
from http.server import ThreadingHTTPServer
from urllib.parse import parse_qs,urlsplit
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
for name in ('desktop','backend','backend/common'):sys.path.insert(0,str(ROOT/name))
from backend import Handler
from connected_browser import ConnectedBrowserBridge
from connected_preparation import ConnectedPreparation

owner=object();sessions={};saved=[];pending=[]


def save(sid,s):
    record={'id':'official-'+__import__('hashlib').sha256(sid.encode()).hexdigest(),'mode':'submit','scope':'official',
        'verdict':s['verdict'],'finishedAt':'2026-11-10T00:00:00+00:00','message':'原站确认提交 #'+s['submissionId']}
    saved.append({'platform':s['platform'],'submissionId':s['submissionId'],'verdict':s['verdict']})
    return record


class Fixture(Handler):
    def do_GET(self):
        target=urlsplit(self.path);q=parse_qs(target.query);bridge=self.server.browser_bridge
        if target.path=='/fixture/create':
            key=q['key'][0];url=q['url'][0]
            self.server.browser_preparation.check_submission(url)
            value=(bridge.open if q.get('manual')==['1'] else bridge.submit)(url,q.get('code',['int main(){}'])[0],key,q.get('language',['cpp17'])[0])
            sessions[key]=value['sessionId'];self.send_json(200,value)
        elif target.path=='/fixture/status':self.send_json(200,{key:bridge.status(sid) for key,sid in sessions.items()})
        elif target.path=='/fixture/ack':self.send_json(200,bridge.acknowledge(sessions[q['key'][0]]))
        elif target.path=='/fixture/saved':self.send_json(200,saved)
        elif target.path=='/fixture/preparation':self.send_json(200,self.server.browser_preparation.snapshot())
        elif target.path=='/fixture/read':
            from contest_reading import ContestReading
            value=ContestReading(bridge,lambda:owner,lambda *_:True)(q['url'][0],owner)
            self.send_json(200,{'length':len(value),'subject':value.count('subject-describe'),'unsafe':'password' in value or 'private-token' in value})
        elif target.path=='/fixture/restore':
            from official_recovery import source_hash
            from test_official_pending_recovery import binding
            record={'sessionId':'recover-fixed','submissionId':'85470558','problemId':'fixture::A','url':'https://ac.nowcoder.com/acm/problem/216116','code':'original fixed source','platform':'牛客','acceptedAt':'2026-11-09T12:00:00+00:00'}
            record['metadata']={'language':'cpp17','codeSha256':source_hash(record['code']),'receiptBinding':binding(record['url'])}
            bridge.restore_pending([record],owner);sessions['restore']=record['sessionId'];self.send_json(200,{'restoring':True})
        elif target.path=='/':
            self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>Foreground fixture</title><p>Keep this tab active</p>')
        else:super().do_GET()


server=ThreadingHTTPServer(('127.0.0.1',0),Fixture);server.frontend_origins=set();server.dist_dir=None
server.store=SimpleNamespace(token='fixture-only')
server.browser_bridge=ConnectedBrowserBridge('http://127.0.0.1:'+str(server.server_port),current_owner=lambda:owner,
    expected_owner=lambda platform:'12345' if platform in ('牛客','洛谷') else 'fixture',on_identity=lambda *_:True,
    on_receipt=save,on_pending=lambda sid,s:pending.append({'sessionId':sid,'submissionId':s.get('submissionId')}) or True)
server.browser_preparation=ConnectedPreparation(server.browser_bridge,ROOT/'build/browser-extension',opener=lambda _:None)
print(json.dumps({'port':server.server_port}),flush=True)
server.serve_forever()
