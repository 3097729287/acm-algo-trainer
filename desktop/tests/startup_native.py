"""Time the normal desktop entry and real signed-in content using isolated data.

The account service is loopback-only, with two independent process launches.
No fixture replaces rendered UI or the public library. Keep evidence for review.
"""
from contextlib import closing
import http.client
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/p) for p in ('desktop','backend','backend/common')]


def child(folder):
    import backend
    import webview
    import launch
    started=float(os.environ['TB_STARTUP_PARENT_CLOCK'])
    result={'mode':'normal user desktop','ok':False,'originalSubmissions':0,'isolatedAccountService':True}
    requests=[]
    original_get=backend.Handler.do_GET
    def timed_get(handler):
        before=time.perf_counter()
        try:return original_get(handler)
        finally:
            if handler.path.startswith('/api/'):
                requests.append({'path':handler.path.split('?',1)[0],'elapsedMs':round((time.perf_counter()-before)*1000,2),'endMs':round((time.perf_counter()-started)*1000,2)})
    backend.Handler.do_GET=timed_get
    original_server=backend.start_server
    def server(**kwargs):
        kwargs['account_endpoint']=os.environ['TB_TEST_ACCOUNTS_ENDPOINT']
        return original_server(**kwargs)
    backend.start_server=server
    original_window=webview.create_window
    def window(*args,**kwargs):
        view=original_window(*args,**kwargs)
        def inspect():
            result['windowShownMs']=round((time.perf_counter()-started)*1000,2)
            def read():
                try:
                    deadline=time.monotonic()+45
                    while time.monotonic()<deadline:
                        value=view.evaluate_js("({shell:!!document.querySelector('.app-shell'),training:[...document.querySelectorAll('.problem-title')].map(x=>x.textContent),login:!!document.querySelector('.account-form'),error:document.querySelector('[role=alert]')?.textContent||''})")
                        if value.get('shell') and any('A+B' in title for title in value['training']):
                            result.update(ok=True,contentShownMs=round((time.perf_counter()-started)*1000,2),trainingTitles=value['training'])
                            break
                        time.sleep(.025)
                    else:result.update(error='Real signed-in training content did not appear',lastDom=value)
                except Exception as error:result['error']=repr(error)
                finally:view.destroy()
            threading.Thread(target=read,name='tb-startup-evidence',daemon=True).start()
        view.events.shown+=inspect
        return view
    webview.create_window=window
    try:result['exitCode']=launch.main([])
    except Exception as error:result['error']=repr(error)
    result['requests']=requests
    (folder/'native-startup.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    return 0 if result['ok'] else 1


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir',type=Path,required=True)
    parser.add_argument('--ui-dist',type=Path)
    parser.add_argument('--library-db',type=Path,help='Reuse a closed public-library fixture in this worktree backups; private account state is always new')
    parser.add_argument('--child',action='store_true')
    args=parser.parse_args();folder=args.work_dir.resolve()
    assert folder.is_relative_to((ROOT/'.backups').resolve())
    if args.child:return child(folder)
    folder.mkdir(parents=True,exist_ok=False)
    state=folder/'state';state.mkdir()
    os.environ.update(TB_STATE_DIR=str(state),TB_OFFLINE='1')
    if args.library_db:
        library=args.library_db.resolve()
        assert library.is_relative_to((ROOT/'.backups/next-150').resolve()) and library.name=='tb-library.sqlite3' and library.is_file()
        assert not library.is_symlink()
        os.environ['TB_LIBRARY_DB']=str(library)
    from backend import create_server
    service=subprocess.Popen(['node',str(ROOT/'server/leaderboard/tests/local-server.mjs')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    server=None
    try:
        endpoint=json.loads(service.stdout.readline())['endpoint']
        server=create_server(account_endpoint=endpoint,integration_auto_start=False)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def call(path,body=None):
            connection=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=45)
            connection.request('GET' if body is None else 'POST','/api/'+path,body=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json','X-TB-Token':server.store.token})
            response=connection.getresponse();result=json.loads(response.read());connection.close()
            assert response.status==200,(path,response.status,result)
            return result
        call('account/register',{'loginId':'startup_native','nickname':'启动验收','password':'isolated-startup-fixture'})
        call('account/login',{'loginId':'startup_native','password':'isolated-startup-fixture'})
        row=next(x for x in server.store.data()['rows'] if x['title']=='A+B Problem')
        server.store.data_response_bytes(compact=True,compressed=True)
        server.training.start_training(row['id']);server.training.save_draft(row['id'],'// preserved isolated startup draft\nint main(){return 0;}')
        preferences=call('preferences')['preferences'] or {}
        preferences.update(onboardingCompleted=True,onboardingGuideVersion=2,levelNoticeVersion=1,levelNoticeSeen=100)
        call('preferences',{'preferences':preferences})
        server.accounts.sync_pending(wait=True)
        database=server.training.db_path
        server.shutdown();server.server_close();thread.join(3);server=None
        reports=[]
        for number in (1,2):
            phase=folder/f'launch-{number}';phase.mkdir()
            env=dict(os.environ,TB_STARTUP_PARENT_CLOCK=str(time.perf_counter()),TB_TEST_ACCOUNTS_ENDPOINT=endpoint,TB_PACKAGE_PORT='0',PYTHONIOENCODING='utf-8')
            if args.ui_dist:env['TB_UI_DIST']=str(args.ui_dist.resolve())
            run=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--work-dir',str(phase),'--child'],env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            (phase/'process.log').write_text(run.stdout+run.stderr,'utf-8')
            assert run.returncode==0,(run.returncode,run.stdout[-1000:],run.stderr[-1000:])
            reports.append(json.loads((phase/'native-startup.json').read_text('utf-8')))
        with closing(__import__('sqlite3').connect(database)) as db:
            assert db.execute('SELECT code FROM drafts WHERE problem_id=?',(row['id'],)).fetchone()[0]=='// preserved isolated startup draft\nint main(){return 0;}'
        result={'ok':True,'launches':reports,'draftPreserved':True,'targetMilliseconds':3000,'targetMet':all(p['contentShownMs']<=3000 for p in reports),'frozen':False,'liveInstallationChanged':False}
        (folder/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    finally:
        if server is not None:server.shutdown();server.server_close()
        service.terminate();service.wait(10);service.stdout.close();service.stderr.close()


if __name__=='__main__':raise SystemExit(main())
