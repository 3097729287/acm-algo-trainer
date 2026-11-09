"""Disposable native APIs for the three-browser team integration check.

Only the isolated shared-service accounts and deterministic judge are used;
this fixture never logs in or submits to an actual problem platform.
"""
import json
import datetime as dt
import os
from pathlib import Path
import sys
import threading

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/p) for p in ('backend','backend/common','desktop')]
from backend import create_server
from training import iso
from test_training import Assets,Judge

if os.environ.get('TB_OFFLINE')!='1':raise RuntimeError('Isolated offline fixture only')
state=Path(os.environ['TB_STATE_DIR']).resolve()
accounts=json.loads(os.environ['TB_TEAM_TEST_ACCOUNTS'])
servers=[];judges=[];threads=[];views=[]
try:
 for i,account in enumerate(accounts):
  local=state/str(i);local.mkdir(parents=True,exist_ok=True)
  table=local/'TB.md'
  table.write_text('| 场次 | 题号 | 题名 | 知识点 | 难度 | 状态 | 日期 |\n|---|---|---|---|---|---|---|\n'+''.join(f'| fixture | {p} | Fixture {p} | 模拟 | 1000 | 未做 | |\n' for p in 'ABC'),encoding='utf8')
  class TeamAssets(Assets):
   def problem(self,identity):
    value=super().problem(identity);value.update(url='https://codeforces.com/contest/123/problem/'+identity.rsplit('::',1)[1],platform='Codeforces',problemType='standard',translationAvailable=False)
    return value
  judge=Judge();judges.append(judge)
  server=create_server(require_account=False,data_file=table,data_root=local,training_file=local/'personal.sqlite3',
    assets=TeamAssets(None),judge=judge,backup_dir=local/'backups',integration_auto_start=False,
    frontend_origins=[os.environ['TB_TEAM_TEST_ORIGIN']])
  original_row=server.training._row
  def team_row(identity,read=original_row):
   row=read(identity);return {**row,'url':'https://codeforces.com/contest/123/problem/'+identity.rsplit('::',1)[1],'platform':'Codeforces'}
  server.training._row=team_row
  # An explicit deterministic native-provider fixture; never a real OJ form.
  native_sessions={};native_log=local/'native-starts.jsonl'
  native_before=len(native_log.read_text('utf8').splitlines()) if native_log.exists() else 0
  def native_submit(url,code,title,language='cpp17',sessions=native_sessions,index=i,log=native_log,before=native_before):
   attempt=before+len(sessions)
   identity=f'isolated-native-{index}-{attempt+1}'
   value={'sessionId':identity,'status':'finished','submissionId':str(900000001+100*index+attempt),
    'verdict':'AC','acceptedAt':iso(dt.datetime.now(dt.timezone.utc)),'platform':'Codeforces','url':url}
   sessions[identity]=value
   with log.open('a',encoding='utf8') as output:output.write(json.dumps({'sessionId':identity,'submissionId':value['submissionId'],'language':language})+'\n')
   return dict(value)
  server.official_submitter=native_submit;server.official_opener=native_submit
  server.official_status=lambda identity,sessions=native_sessions:dict(sessions[identity])
  server.official_closer=lambda identity:{'closed':True}
  server.store.extensions.configure({'accounts':{'codeforces':f'fixture_cf_{i}'}})
  with server.training.lock,server.training._write() as db:
   db.execute('UPDATE ranking_profile SET user_id=?,auth_token=?,endpoint=?',(account['owner'],account['token'],os.environ['TB_TEAM_TEST_ENDPOINT']))
  if not server.training.connection.execute("SELECT 1 FROM drafts WHERE context='' AND problem_id='fixture::A'").fetchone():
   server.training.save_draft('fixture::A',f'private-{i}-untouched')
  servers.append(server);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();threads.append(thread)
  views.append({'owner':account['owner'],'endpoint':f'http://127.0.0.1:{server.server_port}','token':server.store.token})
 print(json.dumps(views),flush=True)
 for line in sys.stdin:
  if line.strip()=='stop':break
finally:
 for judge in judges:judge.release.set()
 for server in servers:server.shutdown();server.server_close()
 for thread in threads:thread.join(3)
